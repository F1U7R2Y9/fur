#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

{% for standard_library in standard_libraries %}
#include <{{standard_library}}>
{% endfor %}

enum Type;
typedef enum Type Type;
union Instance;
typedef union Instance Instance;
struct Object;
typedef struct Object Object;

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

union Instance
{
  bool boolean;
  Object (*closure)(size_t, Object*);
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
    // No objects are allocated on the heap (yet!) so we don't need to free anything else
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
    // We can compare pointers because pointers are unique in the SYMBOL_LIST
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

Object operator$add(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer + right.instance.integer;
  return result;
}

Object operator$subtract(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer - right.instance.integer;
  return result;
}

Object operator$multiply(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer * right.instance.integer;
  return result;
}

Object operator$integerDivide(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer / right.instance.integer;
  return result;
}

Object operator$modularDivide(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.instance.integer = left.instance.integer % right.instance.integer;
  return result;
}

Object operator$equals(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer == right.instance.integer };
  return result;
}

Object operator$notEquals(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer != right.instance.integer };
  return result;
}

Object operator$greaterThan(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer > right.instance.integer };
  return result;
}

Object operator$lessThan(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer < right.instance.integer };
  return result;
}

Object operator$greaterThanOrEqual(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer >= right.instance.integer };
  return result;
}

Object operator$lessThanOrEqual(Object left, Object right)
{
  assert(left.type == INTEGER);
  assert(right.type == INTEGER);

  Object result = { BOOLEAN, left.instance.integer <= right.instance.integer };
  return result;
}

Object operator$and(Object left, Object right)
{
  assert(left.type == BOOLEAN);
  assert(right.type == BOOLEAN);

  Object result = { BOOLEAN, left.instance.boolean && right.instance.boolean };
  return result;
}

Object operator$or(Object left, Object right)
{
  assert(left.type == BOOLEAN);
  assert(right.type == BOOLEAN);

  Object result = { BOOLEAN, left.instance.boolean || right.instance.boolean };
  return result;
}

{% if 'pow' in builtins %}
Object builtin$pow$implementation(size_t argc, Object* args)
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

Object builtin$pow = { CLOSURE, (Instance)builtin$pow$implementation };
{% endif %}

{% if 'print' in builtins %}
Object builtin$print$implementation(size_t argc, Object* args)
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

Object builtin$print = { CLOSURE, (Instance)builtin$print$implementation };
{% endif %}

int main(int argc, char** argv)
{
  Environment* environment = Environment_construct();

  // TODO Use the symbol from SYMBOL_LIST
  {% for builtin in builtins %}
  Environment_set(environment, "{{ builtin }}", builtin${{ builtin }});
  {% endfor %}

  {% for statement in statements %}
  {{ statement }}
  {% endfor %}

  Environment_destruct(environment);

  return 0;
}
