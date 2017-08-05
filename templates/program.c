#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

{% for standard_library in standard_libraries %}
#include <{{standard_library}}>
{% endfor %}

struct String;
typedef struct String String;
enum Type;
typedef enum Type Type;
union Instance;
typedef union Instance Instance;
struct Object;
typedef struct Object Object;
struct Runtime;
typedef struct Runtime Runtime;

struct String
{
  size_t length;
  char* characters;
};

#define MAX_SYMBOL_LENGTH {{ MAX_SYMBOL_LENGTH }}
struct Symbol;
typedef struct Symbol Symbol;
struct Symbol
{
  size_t length;
  char name[MAX_SYMBOL_LENGTH];
};

enum Type
{
  INTEGER,
  STRING
};

union Instance
{
  int32_t integer;
  String* string;
};

struct Object
{
  Type type;
  Instance instance;
};

struct EnvironmentNode;
typedef struct EnvironmentNode EnvironmentNode;
struct EnvironmentNode
{
  Symbol* key;
  Object value;
  EnvironmentNode* next;
};

struct Environment;
typedef struct Environment Environment;
struct Environment
{
  EnvironmentNode* root;
};

Environment* Environment_construct()
{
  // TODO Handle malloc returning NULL
  Environment* result = malloc(sizeof(Environment));
  result->root = NULL;
  return result;
}

void Environment_destruct(Environment* self)
{
  EnvironmentNode* next;
  for(EnvironmentNode* node = self->root; node != NULL; node = next)
  {
    // We don't need to destruct the keys, because those will be destructed at the end when the Runtime is destructed
    // We don't need to destruct the permanent strings, because those will be destructed at the end when the Runtime is destructed
    // The above two comments represent all heap-allocated objects currently, so we don't need to destruct Objects (yet)
    next = node->next;
    free(node);
  }
}

// This need not be thread safe because environments exist on one thread only
void Environment_set(Environment* self, Symbol* key, Object value)
{
  EnvironmentNode* node = malloc(sizeof(EnvironmentNode));
  node->key = key;
  node->value = value;
  node->next = self->root;
  self->root = node;
}

Object Environment_get(Environment* self, Symbol* symbol)
{
  for(EnvironmentNode* node = self->root; node != NULL; node = node->next)
  {
    // We can compare pointers because pointers are unique within Runtime->symbols
    if(node->key == symbol)
    {
      return node->value;
    }
  }

  // TODO Handle symbol errors
  assert(false);
}


// TODO Allocate all symbols and strings as static constants so we can remove the level of indirection
struct Runtime
{
  size_t permanentStringsLength;
  size_t permanentStringsAllocated;
  String** permanentStrings;
  size_t symbolsLength;
  size_t symbolsAllocated;
  Symbol** symbols;
};

Runtime* Runtime_construct()
{
  Runtime* result = malloc(sizeof(Runtime));
  result->permanentStringsLength = 0;
  result->permanentStringsAllocated = 0;
  result->permanentStrings = NULL;
  result->symbolsLength = 0;
  result->symbolsAllocated =0;
  result->symbols = NULL;
  return result;
}

void Runtime_destruct(Runtime* self)
{
  for(size_t i = 0; i < self->permanentStringsLength; i++)
  {
    free(self->permanentStrings[i]);
  }

  for(size_t i = 0; i < self->symbolsLength; i++)
  {
    free(self->symbols[i]);
  }

  free(self->permanentStrings);
  free(self->symbols);
  free(self);
}

void Runtime_addPermanentString(Runtime* self, String* string)
{
  // TODO Make this function thread-safe
  if(self->permanentStringsLength == self->permanentStringsAllocated)
  {
    if(self->permanentStringsAllocated == 0)
    {
      self->permanentStringsAllocated = 8;
    }
    else
    {
      self->permanentStringsAllocated = self->permanentStringsAllocated * 2;
    }

    self->permanentStrings = realloc(
      self->permanentStrings,
      sizeof(String*) * self->permanentStringsAllocated
    );

    // TODO Handle realloc returning NULL
  }

  self->permanentStrings[self->permanentStringsLength] = string;
  self->permanentStringsLength++;
}

// TODO Optimize this by sorting the symbols
// TODO Make this function thread safe
Symbol* Runtime_symbol(Runtime* self, const char* name)
{
  assert(strlen(name) <= MAX_SYMBOL_LENGTH);

  for(size_t i = 0; i < self->symbolsLength; i++)
  {
    if(strcmp(self->symbols[i]->name, name) == 0)
    {
      return self->symbols[i];
    }
  }

  if(self->symbolsLength == self->symbolsAllocated)
  {
    if(self->symbolsAllocated == 0)
    {
      self->symbolsAllocated = 8;
    }
    else
    {
      self->symbolsAllocated = self->symbolsAllocated * 2;
    }

    self->symbols = realloc(
      self->symbols,
      sizeof(Symbol*) * self->symbolsAllocated
    );

    // TODO Handle realloc returning NULL
  }

  Symbol* result = malloc(sizeof(Symbol));
  result->length = strlen(name);
  strcpy(result->name, name);

  self->symbols[self->symbolsLength] = result;
  self->symbolsLength++;

  return result;
}

Object integerLiteral(int32_t literal)
{
  Object result;
  result.type = INTEGER;
  result.instance.integer = literal;
  return result;
}

Object stringLiteral(Runtime* runtime, const char* literal)
{
  String* resultString = malloc(sizeof(String));
  resultString->length = strlen(literal);
  resultString->characters = malloc(resultString->length);
  memcpy(resultString->characters, literal, resultString->length);
  Runtime_addPermanentString(runtime, resultString);

  Object result;
  result.type = STRING;
  result.instance.string = resultString;
  return result;
}

// TODO Make this conditionally added
Object builtin$negate(Object input)
{
  assert(input.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = -input.instance.integer;
  return result;
}

Object builtin$add(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer + right.instance.integer;
  return result;
}

Object builtin$subtract(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer - right.instance.integer;
  return result;
}

Object builtin$multiply(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer * right.instance.integer;
  return result;
}

Object builtin$integerDivide(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer / right.instance.integer;
  return result;
}

Object builtin$modularDivide(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer % right.instance.integer;
  return result;
}

{% if 'pow' in builtins %}
Object builtin$pow(Object base, Object exponent)
{
  assert(base.type == INTEGER);
  assert(exponent.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = pow(base.instance.integer, exponent.instance.integer);
  return result;
}
{% endif %}

{% if 'print' in builtins %}
void builtin$print(Object output)
{
  switch(output.type)
  {
    case INTEGER:
      printf("%" PRId32, output.instance.integer);
      break;

    case STRING:
      // Using fwrite instead of printf to handle size_t length
      fwrite(output.instance.string->characters, 1, output.instance.string->length, stdout);
      break;

    default:
      assert(false);
  }
}
{% endif %}

int main(int argc, char** argv)
{
  Runtime* runtime = Runtime_construct();
  Environment* environment = Environment_construct();

  {% for statement in statements %}
  {{ statement }}
  {% endfor %}

  Environment_destruct(environment);
  Runtime_destruct(runtime);

  return 0;
}
