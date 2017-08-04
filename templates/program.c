#include <stdlib.h>
#include <string.h>

{% for standard_library in standard_libraries %}
#include <{{standard_library}}>
{% endfor %}

struct String;
typedef struct String String;
struct Runtime;
typedef struct Runtime Runtime;

struct String
{
  size_t length;
  char* characters;
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

String* stringLiteral(Runtime* runtime, const char* literal)
{
  String* result = malloc(sizeof(String));
  result->length = strlen(literal);
  result->characters = malloc(result->length);
  memcpy(result->characters, literal, result->length);
  Runtime_addPermanentString(runtime, result);
  return result;
}

{% if 'print' in builtins %}
void builtin$print(String* output)
{
  // Using fwrite instead of printf to handle size_t length
  fwrite(output->characters, 1, output->length, stdout);
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
