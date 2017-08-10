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
  STRING
};

struct Closure;
typedef struct Closure Closure;
struct Closure
{
  Object (*call)(EnvironmentPool*, Environment*, size_t, Object*);
};

union Instance
{
  bool boolean;
  Closure closure;
  int32_t integer;
  const char* string;
};

struct Object
{
  Type type;
  Instance instance;
};

const Object TRUE = {
  BOOLEAN,
  { true }
};

const Object FALSE = {
  BOOLEAN,
  { false }
};

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

void Environment_deinitialize(Environment* self)
{
  EnvironmentNode* next;
  for(EnvironmentNode* node = self->root; node != NULL; node = next)
  {
    next = node->next;
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
  result.type = STRING;
  result.instance.string = literal;
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
Object builtin$pow$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Object* args)
{
  assert(argc == 2);

  Object base = args[0];
  Object exponent = args[1];

  assert(base.type == INTEGER);
  assert(exponent.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = pow(base.instance.integer, exponent.instance.integer);
  return result;
}

Object builtin$pow = { CLOSURE, (Instance)(Closure){ builtin$pow$implementation } };
{% endif %}

{% if 'print' in builtins %}
Object builtin$print$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Object* args)
{
  for(size_t i = 0; i < argc; i++)
  {
    Object output = args[i];
    switch(output.type)
    {
      case BOOLEAN:
        fputs(output.instance.boolean ? "true" : "false", stdout);
        break;

      case INTEGER:
        printf("%" PRId32, output.instance.integer);
        break;

      case STRING:
        // Using fwrite instead of printf to handle size_t length
        printf("%s", output.instance.string);
        break;

      default:
        assert(false);
    }
  }

  // TODO Return something better
  return FALSE;
}

Object builtin$print = { CLOSURE, (Instance)(Closure){ builtin$print$implementation } };
{% endif %}

{% for function_definition in function_definition_list %}
Object user${{function_definition.name}}$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Object* args)
{
  Environment* environment = EnvironmentPool_allocate(environmentPool);
  Environment_initialize(environment, parent);

  {% for statement in function_definition.statement_list[:-1] %}
  {{ generate_statement(statement) }}
  {% endfor %}

  Object result = {{ generate_statement(function_definition.statement_list[-1]) }}

  Environment_setLive(environment, false);
  return result;
}

{% endfor %}
int main(int argc, char** argv)
{
  EnvironmentPool* environmentPool = EnvironmentPool_construct();
  Environment* environment = EnvironmentPool_allocate(environmentPool);
  Environment_initialize(environment, NULL);

  // TODO Use the symbol from SYMBOL_LIST
  {% for builtin in builtins %}
  Environment_set(environment, "{{ builtin }}", builtin${{ builtin }});
  {% endfor %}

  {% for statement in statements %}
  {{ generate_statement(statement) }}
  {% endfor %}

  Environment_setLive(environment, false);
  EnvironmentPool_destruct(environmentPool);
  return 0;
}
