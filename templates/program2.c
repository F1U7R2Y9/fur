#include<assert.h>
#include<stdbool.h>
#include<stdint.h>
#include<stdio.h>
#include<stdlib.h>
#include<string.h>

enum Type;
typedef enum Type Type;
enum Type {
  BUILTIN,
  INTEGER,
  STRING
};

enum Builtin;
typedef enum Builtin Builtin;
enum Builtin {
  NIL,
  PRINT
};

union Value;
typedef union Value Value;
union Value {
  Builtin builtin;
  char* string;
  int32_t integer;
};

struct Object;
typedef struct Object Object;
struct Object {
  Type type;
  Value value;
};

#define BUILTIN_NIL (Object) { BUILTIN, (Value)(Builtin)NIL }

void Object_deinitialize(Object* self) {
}

{% include "environment.c" %}
{% include "stack.c" %}

struct Thread;
typedef struct Thread Thread;
struct Thread {
  Environment* environment;
  Stack stack;
  size_t program_counter;
};

void Thread_initialize(Thread* self, size_t program_counter) {
  self->environment = Environment_construct();
  Stack_initialize(&(self->stack));
  self->program_counter = program_counter;
}

void Thread_deinitialize(Thread* self) {
  Environment_destruct(self->environment);
  Stack_deinitialize(&(self->stack));
}

union Argument;
typedef const union Argument Argument;
union Argument {
  size_t label;
  void* pointer;
  char* string;
  int32_t integer;
};

void call(struct Thread* thread, const union Argument argument) {
  assert(!Stack_isEmpty(&(thread->stack)));
  Object f = Stack_pop(&(thread->stack));

  switch(f.type) {
    case BUILTIN:
      switch(f.value.builtin) {
        case PRINT:
          {
            // TODO Handle multiple arguments
            assert(!Stack_isEmpty(&(thread->stack)));
            Object arg = Stack_pop(&(thread->stack));

            switch(arg.type) {
              case INTEGER:
                printf("%i", arg.value.integer);
                break;

              case STRING:
                printf("%s", arg.value.string);
                break;

              default:
                assert(0);
            }

            Stack_push(&(thread->stack), BUILTIN_NIL);
          }
          break;

        default:
          assert(false);
      }
      break;

    default:
      assert(false);
  }
}

{% with name='add', operation='+' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}


void drop(struct Thread* thread, const union Argument argument) {
  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));
  Object_deinitialize(&result);
}

void end(struct Thread* thread, const union Argument argument) {
}

{% with name='idiv', operation='/' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

{% with name='mod', operation='%' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

{% with name='mul', operation='*' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

void pop(struct Thread* thread, const union Argument argument) {
  char* argumentString = argument.string;

  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));

  if(strcmp(argumentString, "print") == 0) {
    assert(false);
  }

  Environment_set(thread->environment, argumentString, result);
}

void push(struct Thread* thread, const union Argument argument) {
  char* argumentString = argument.string;

  if(strcmp(argumentString, "print") == 0) {
    Object result;
    result.type = BUILTIN;
    result.value.builtin = PRINT;
    Stack_push(&(thread->stack), result);
  } else {
    Environment_get_Result result = Environment_get(thread->environment, argumentString);
    if(!result.found) {
      fprintf(stderr, "Variable `%s` not found", argumentString);
      assert(false);
    }
    Stack_push(&(thread->stack), result.result);
  }
}

void push_integer(struct Thread* thread, const union Argument argument) {
  Object result;
  result.type = INTEGER;
  result.value.integer = argument.integer;

  Stack_push(&(thread->stack), result);
}

void push_string(struct Thread* thread, const union Argument argument) {
  Object result;
  result.type = STRING;
  result.value.string = argument.string;

  Stack_push(&(thread->stack), result);
}

{% with name='sub', operation='-' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

struct Instruction;
typedef const struct Instruction Instruction;
struct Instruction {
  void (*instruction)(struct Thread*,const union Argument);
  Argument argument;
};

{% for label in labels_to_instruction_indices.keys() %}
#define LABEL_{{ label }} {{ labels_to_instruction_indices[label] }}
{% endfor %}

const Instruction program[] = {
{% for instruction in instruction_list %}
  (Instruction){ {{ instruction.instruction }}, (Argument){{ generate_argument(instruction) }} },
{% endfor %}
};

int main() {
  Thread thread;
  Thread_initialize(&thread, 0);

  for(; program[thread.program_counter].instruction != end; thread.program_counter++) {
    program[thread.program_counter].instruction(
      &thread,
      program[thread.program_counter].argument
    );
  }

  Thread_deinitialize(&thread);

  return 0;
}