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

struct Runtime
{
  size_t permanentStringsLength;
  size_t permanentStringsAllocated;
  String** permanentStrings;
};

Runtime* Runtime_construct()
{
  Runtime* result = malloc(sizeof(Runtime));
  result->permanentStringsLength = 0;
  result->permanentStringsAllocated = 0;
  result->permanentStrings = NULL;
  return result;
}

void Runtime_destruct(Runtime* self)
{
  free(self->permanentStrings);
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

  {% for statement in statements %}
  {{ statement }}
  {% endfor %}

  Runtime_destruct(runtime);

  return 0;
}
