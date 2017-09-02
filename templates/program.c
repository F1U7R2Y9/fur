#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

/* Some terminology used in function names:
 * - initialize: These functions take a pointer and potentially some other arguments, and use those
 *   to initialize the value pointed to by self. Initialize functions DO NOT allocate the function,
 *   so they can be used to initialize stack-allocated variables.
 * - construct: This allocates a value for a pointer, initializes it, and returns it. This is for
 *   heap-allocated values. It may be as simple as allocating the memory, calling an initialize, and
 *   returning it.
 * - deinitialize: These functions dereference or free any objects pointed to by the self pointer's
 *   value, but they don't actually free the self pointer. This is useful for stack-allocated objects
 *   which point to heap-allocated objects.
 * - destruct: This dereferences or frees memory pointed to by the self argument, and all the
 *   pointers on the self argument.
 */

{% for standard_library in standard_libraries %}
#include <{{standard_library}}>
{% endfor %}

enum Type;
typedef enum Type Type;
union Instance;
typedef union Instance Instance;
struct Object;
typedef struct Object Object;
struct EnvironmentNode;
typedef struct EnvironmentNode EnvironmentNode;
struct Environment;
typedef struct Environment Environment;
struct EnvironmentPool;
typedef struct EnvironmentPool EnvironmentPool;
struct Stack;
typedef struct Stack Stack;

const char* const STRING_LITERAL_LIST[] = {
{% for string_literal in string_literal_list %}
  "{{ string_literal }}",
{% endfor %}
};

const char* const SYMBOL_LIST[] = {
{% for symbol in symbol_list %}
  "{{ symbol }}",
{% endfor %}
};

enum Type
{
  BOOLEAN,
  CLOSURE,
  INTEGER,
  LIST,
  STRING_CONCATENATION,
  STRING_LITERAL,
  STRUCTURE,
  VOID
};

struct Closure;
typedef struct Closure Closure;
struct Closure
{
  Environment* closed;
  Object (*call)(EnvironmentPool*, Environment*, size_t, Stack*);
};

struct List;
typedef struct List List;
struct List
{
  size_t allocated;
  size_t length;
  Object* items;
};

struct StringConcatenation;
typedef struct StringConcatenation StringConcatenation;

struct Structure;
typedef struct Structure Structure;
struct Structure
{
  size_t reference_count;
  size_t length;
  const char** symbol_list;
  Object* value_list;
};

union Instance
{
  bool boolean;
  Closure closure;
  int32_t integer;
  List list;
  StringConcatenation* string_concatenation;
  const char* string_literal;
  Structure* structure;
};

struct Object
{
  Type type;
  Instance instance;
};

const Object builtin$true = { BOOLEAN, (Instance)(bool){ true } };
const Object builtin$false = { BOOLEAN, (Instance)(bool){ false } };
const Object builtin$nil = { VOID, { 0 } };

struct StringConcatenation
{
  size_t referenceCount;
  Object left;
  Object right;
};

Object List_construct(size_t allocate)
{
  Object* items = malloc(sizeof(Object) * allocate);
  Object result = { LIST, (Instance)(List){ allocate, 0, items } };
  return result;
}

void List_append(Object* list, Object item)
{
  assert(list->type == LIST);

  if(list->instance.list.allocated == list->instance.list.length)
  {
    list->instance.list.allocated *= 2;
    list->instance.list.items = realloc(
      list->instance.list.items,
      sizeof(Object) * list->instance.list.allocated
    );
  }

  list->instance.list.items[list->instance.list.length] = item;
  list->instance.list.length++;
}

Object List_get(Object* list, Object index)
{
  assert(list->type == LIST);
  assert(index.type == INTEGER);

  return list->instance.list.items[index.instance.integer];
}

struct Stack
{
  uint16_t length;
  Object items[256];
};

void Stack_initialize(Stack* self)
{
  self->length = 0;
}

void Stack_push(Stack* self, Object item)
{
  assert(self->length < 256);
  self->items[self->length] = item;
  self->length++;
}

Object Stack_pop(Stack* self)
{
  assert(self->length > 0);
  self->length--;
  return self->items[self->length];
}

Object Object_rereference(Object self)
{
  switch(self.type)
  {
    case BOOLEAN:
    case CLOSURE:
    case INTEGER:
    case STRING_LITERAL:
    case VOID:
      return self;

    case STRING_CONCATENATION:
      self.instance.string_concatenation->referenceCount++;
      return self;

    case STRUCTURE:
      self.instance.structure->reference_count++;
      return self;

    default:
      assert(false);
  }
}

Object Structure_construct(size_t length, const char** symbol_list, Object* value_list)
{
  Structure* structure = malloc(sizeof(Structure));
  structure->reference_count = 1;
  structure->length = length;
  structure->symbol_list = malloc(sizeof(const char*) * length);
  structure->value_list = malloc(sizeof(Object) * length);

  // TODO Don't allow assignment of mutable structures, as this screws up reference counting
  for(size_t i = 0; i < length; i++)
  {
    structure->symbol_list[i] = symbol_list[i];
    structure->value_list[i] = Object_rereference(value_list[i]);
  }

  Object result = { STRUCTURE, (Instance)structure };

  return result;
}

Object Structure_get(Object* self, const char* symbol)
{
  assert(self->type == STRUCTURE);

  for(size_t i = 0; i < self->instance.structure->length; i++)
  {
    if(self->instance.structure->symbol_list[i] == symbol)
    {
      return self->instance.structure->value_list[i];
    }
  }

  assert(false);
}

struct EnvironmentNode
{
  const char* key;
  Object value;
  EnvironmentNode* next;
};

struct Environment
{
  bool mark;
  bool live;

  Environment* parent;
  EnvironmentNode* root;
};

void Environment_initialize(Environment* self, Environment* parent)
{
  self->parent = parent;
  self->root = NULL;

  // We are currently only ever initializing environments at the beginning of running functions, so
  // for now at least we can assume that we want it to be live immediately.
  self->live = true;
}

void Object_deinitialize(Object* self)
{
  switch(self->type)
  {
    case BOOLEAN:
      break;
    case CLOSURE:
      break;
    case INTEGER:
      break;
    case STRING_LITERAL:
      break;
    case VOID:
      break;

    case LIST:
      for(size_t i = 0; i < self->instance.list.length; i++) {
        Object_deinitialize(&(self->instance.list.items[i]));
      }

      free(self->instance.list.items);
      break;

    case STRING_CONCATENATION:
      self->instance.string_concatenation->referenceCount--;

      if(self->instance.string_concatenation->referenceCount == 0)
      {
        Object_deinitialize(&(self->instance.string_concatenation->left));
        Object_deinitialize(&(self->instance.string_concatenation->right));
        free(self->instance.string_concatenation);
      }
      break;

    case STRUCTURE:
      self->instance.structure->reference_count--;

      if(self->instance.structure->reference_count == 0)
      {
        for(size_t i = 0; i < self->instance.structure->length; i++)
        {
          Object_deinitialize(&(self->instance.structure->value_list[i]));
        }
        free(self->instance.structure->symbol_list);
        free(self->instance.structure->value_list);
        free(self->instance.structure);
      }
      break;

    default:
      assert(false);
  }
}

void Environment_deinitialize(Environment* self)
{
  EnvironmentNode* next;
  for(EnvironmentNode* node = self->root; node != NULL; node = next)
  {
    next = node->next;
    Object_deinitialize(&(node->value));
    free(node);
  }
}

void Environment_setLive(Environment* self, bool live)
{
  self->live = live;
}

void Environment_mark(Environment* self)
{
  if(self == NULL) return;
  if(self->mark) return; // Prevents infinite recursion in the case of cycles

  self->mark = true;

  Environment_mark(self->parent);

  for(EnvironmentNode* node = self->root; node != NULL; node = node->next)
  {
    switch(node->value.type)
    {
      case BOOLEAN:
      case INTEGER:
      case STRING_LITERAL:
      case VOID:
        break;

      case CLOSURE:
        Environment_mark(node->value.instance.closure.closed);
        break;

      default:
        assert(false);
    }
  }
}

// This need not be thread safe because environments exist on one thread only
void Environment_set(Environment* self, const char* const key, Object value)
{
  EnvironmentNode* node = malloc(sizeof(EnvironmentNode));
  node->key = key;
  node->value = value;
  node->next = self->root;
  self->root = node;
}

Object Environment_get(Environment* self, const char* const symbol)
{
  for(EnvironmentNode* node = self->root; node != NULL; node = node->next)
  {
    // We can compare pointers because pointers are unique in the SYMBOL_LIST
    if(node->key == symbol)
    {
      return node->value;
    }
  }

  if(self->parent != NULL)
  {
    return Environment_get(self->parent, symbol);
  }

  // TODO Handle symbol errors
  assert(false);
}

# define POOL_SIZE 64
struct EnvironmentPool
{
  int8_t freeIndex;
  bool allocatedFlags[POOL_SIZE];
  Environment environments[POOL_SIZE];
  EnvironmentPool* overflow;
};

EnvironmentPool* EnvironmentPool_construct();
void EnvironmentPool_initialize(EnvironmentPool*);
void EnvironmentPool_deinitialize(EnvironmentPool*);
void EnvironmentPool_destruct(EnvironmentPool*);

EnvironmentPool* EnvironmentPool_construct()
{
  EnvironmentPool* result = malloc(sizeof(EnvironmentPool));
  EnvironmentPool_initialize(result);
  return result;
}

void EnvironmentPool_initialize(EnvironmentPool* self)
{
  self->overflow = NULL;
  self->freeIndex = 0;

  for(size_t i = 0; i < POOL_SIZE; i++)
  {
    self->allocatedFlags[i] = false;
    self->environments[i].live = false;
  }
}

void EnvironmentPool_deinitialize(EnvironmentPool* self)
{
  // We can assume if this is being called, none of the Environments are live
  for(int8_t i = 0; i < POOL_SIZE; i++)
  {
    if(self->allocatedFlags[i]) Environment_deinitialize(&(self->environments[i]));
  }

  EnvironmentPool_destruct(self->overflow);
}

void EnvironmentPool_destruct(EnvironmentPool* self)
{
  if(self == NULL) return;
  EnvironmentPool_deinitialize(self);
  free(self);
}

void EnvironmentPool_GC(EnvironmentPool* self)
{
  // Unmark all the environments
  for(EnvironmentPool* current = self; current != NULL; current = current->overflow)
  {
    for(int8_t i = 0; i < POOL_SIZE; i++)
    {
      current->environments[i].mark = false;
    }
  }

  // Mark live enviroments and environments referenced by live environments
  for(EnvironmentPool* current = self; current != NULL; current = current->overflow)
  {
    for(int8_t i = 0; i < POOL_SIZE; i++)
    {
      if(current->environments[i].live)
      {
        Environment_mark(&(current->environments[i]));
      }
    }
  }

  // TODO We never free pools until the very end--we could free a pool if two pools are empty
  for(EnvironmentPool* current = self; current != NULL; current = current->overflow)
  {
    for(int8_t i = POOL_SIZE - 1; i >= 0; i--)
    {
      if(!current->environments[i].mark && current->allocatedFlags[i])
      {
        Environment_deinitialize(&(current->environments[i]));
        current->allocatedFlags[i] = false;
        current->freeIndex = i;
      }
    }
  }
}

Environment* EnvironmentPool_allocate(EnvironmentPool* self)
{
  for(EnvironmentPool* current = self; current != NULL; current = current->overflow)
  {
    for(; current->freeIndex < POOL_SIZE; current->freeIndex++)
    {
      if(!current->allocatedFlags[current->freeIndex])
      {
        current->allocatedFlags[current->freeIndex] = true;
        return &(current->environments[current->freeIndex]);
      }
    }
  }

  EnvironmentPool_GC(self);

  EnvironmentPool* previous;
  for(EnvironmentPool* current = self; current != NULL; current = current->overflow)
  {
    for(; current->freeIndex < POOL_SIZE; current->freeIndex++)
    {
      if(!current->allocatedFlags[current->freeIndex])
      {
        current->allocatedFlags[current->freeIndex] = true;
        return &(current->environments[current->freeIndex]);
      }
      else
      {
        previous = current;
      }
    }
  }

  previous->overflow = EnvironmentPool_construct();
  return EnvironmentPool_allocate(previous->overflow);
}

Object integerLiteral(int32_t literal)
{
  Object result;
  result.type = INTEGER;
  result.instance.integer = literal;
  return result;
}

Object stringLiteral(const char* literal)
{
  Object result;
  result.type = STRING_LITERAL;
  result.instance.string_literal = literal;
  return result;
}

// TODO Make this conditionally added
Object operator$negate(Object input)
{
  assert(input.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = -input.instance.integer;
  return result;
}

// TODO Make this conditionally added
Object operator$concatenate(Object left, Object right)
{
  switch(left.type) {
    case STRING_CONCATENATION:
    case STRING_LITERAL:
      break;

    default:
      assert(false);
  }

  switch(right.type) {
    case STRING_CONCATENATION:
    case STRING_LITERAL:
      break;

    default:
      assert(false);
  }

  StringConcatenation* concatenation = malloc(sizeof(StringConcatenation));
  concatenation->referenceCount = 1;
  concatenation->left = Object_rereference(left);
  concatenation->right = Object_rereference(right);

  Object result = { STRING_CONCATENATION, (Instance)concatenation };
  return result;
}

{% for id in infix_declarations %}
Object operator${{ id.name }}(Object left, Object right)
{
  assert(left.type == {{ id.in_type.upper() }});
  assert(right.type == {{ id.in_type.upper() }});

  Object result;
  result.type = {{ id.out_type.upper() }};
  result.instance.{{ id.out_type.lower() }} = left.instance.{{ id.in_type.lower() }} {{ id.operator }} right.instance.{{ id.in_type.lower() }};
  return result;
}
{% endfor %}

{% if 'pow' in builtins %}
Object builtin$pow$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Stack* stack)
{
  // Must unload items in reverse order
  Object exponent = Stack_pop(stack);
  Object base = Stack_pop(stack);

  assert(base.type == INTEGER);
  assert(exponent.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = pow(base.instance.integer, exponent.instance.integer);
  return result;
}

Object builtin$pow = { CLOSURE, (Instance)(Closure){ NULL, builtin$pow$implementation } };
{% endif %}

{% if 'print' in builtins %}
Object builtin$print$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Stack* stack)
{
  Stack reverse_stack;
  Stack_initialize(&reverse_stack);

  for(size_t i = 0; i < argc; i++)
  {
    Stack_push(&reverse_stack, Stack_pop(stack));
  }

  while(reverse_stack.length > 0)
  {
    Object output = Stack_pop(&reverse_stack);
    switch(output.type)
    {
      case BOOLEAN:
        fputs(output.instance.boolean ? "true" : "false", stdout);
        break;

      case CLOSURE:
        // TODO Print something better
        printf("<Closure>");
        break;

      case INTEGER:
        printf("%" PRId32, output.instance.integer);
        break;

      case STRING_CONCATENATION:
        Stack_push(stack, output.instance.string_concatenation->left);
        builtin$print$implementation(NULL, NULL, 1, stack);
        Stack_push(stack, output.instance.string_concatenation->right);
        builtin$print$implementation(NULL, NULL, 1, stack);
        break;

      case STRING_LITERAL:
        // Using fwrite instead of printf to handle size_t length
        printf("%s", output.instance.string_literal);
        break;

      case VOID:
        printf("nil");
        break;

      default:
        assert(false);
    }
    Object_deinitialize(&output);
  }

  // TODO Return something better
  return builtin$false;
}

Object builtin$print = { CLOSURE, (Instance)(Closure){ NULL, builtin$print$implementation } };
{% endif %}
{% for function_definition in function_definition_list %}
{{ function_definition }}
{% endfor %}

int main(int argc, char** argv)
{
  EnvironmentPool* environmentPool = EnvironmentPool_construct();
  Environment* environment = EnvironmentPool_allocate(environmentPool);
  Environment_initialize(environment, NULL);

  Stack stackMemory;
  Stack* stack = &stackMemory;
  Stack_initialize(stack);

  // TODO Use the symbol from SYMBOL_LIST
  {% for builtin in builtins %}
  Environment_set(environment, "{{ builtin }}", builtin${{ builtin }});
  {% endfor %}

  {% for statement in statements %}
  {{ statement }}
  {% endfor %}

  Environment_setLive(environment, false);
  EnvironmentPool_destruct(environmentPool);
  return 0;
}
