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

const char * const SYMBOL_LIST[] = {
{% for symbol in symbol_list %}
  "{{ symbol }}",
{% endfor %}
};

enum Type
{
  BOOLEAN,
  INTEGER,
  STRING
};

union Instance
{
  bool boolean;
  int32_t integer;
  char* string;
};

struct Object
{
  Type type;
  Instance instance;
};

const Object TRUE = {
  BOOLEAN,
  true
};

const Object FALSE = {
  BOOLEAN,
  false
};

struct EnvironmentNode;
typedef struct EnvironmentNode EnvironmentNode;
struct EnvironmentNode
{
  const char* key;
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
    // We don't need to destruct the permanent strings, because those will be destructed at the end when the Runtime is destructed
    // The above comment represents all heap-allocated objects currently, so we don't need to destruct Objects (yet)
    next = node->next;
    free(node);
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
    // We can compare pointers because pointers are unique in the SYMBOLS_LIST
    if(node->key == symbol)
    {
      return node->value;
    }
  }

  // TODO Handle symbol errors
  assert(false);
}

Object integerLiteral(int32_t literal)
{
  Object result;
  result.type = INTEGER;
  result.instance.integer = literal;
  return result;
}

Object stringLiteral(char* literal)
{
  Object result;
  result.type = STRING;
  result.instance.string = literal;
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

Object builtin$equals(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer == right.instance.integer };
  return result;
}

Object builtin$notEquals(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer != right.instance.integer };
  return result;
}

Object builtin$greaterThan(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer > right.instance.integer };
  return result;
}

Object builtin$lessThan(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer < right.instance.integer };
  return result;
}

Object builtin$greaterThanOrEqual(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer >= right.instance.integer };
  return result;
}

Object builtin$lessThanOrEqual(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer <= right.instance.integer };
  return result;
}

Object builtin$and(Object left, Object right)
{
  assert(left.type == BOOLEAN);
  assert(right.type == BOOLEAN);

  Object result = { BOOLEAN, left.instance.boolean && right.instance.boolean };
  return result;
}

Object builtin$or(Object left, Object right)
{
  assert(left.type == BOOLEAN);
  assert(right.type == BOOLEAN);

  Object result = { BOOLEAN, left.instance.boolean || right.instance.boolean };
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
{% endif %}

int main(int argc, char** argv)
{
  Environment* environment = Environment_construct();

  {% for statement in statements %}
  {{ statement }}
  {% endfor %}

  Environment_destruct(environment);

  return 0;
}
