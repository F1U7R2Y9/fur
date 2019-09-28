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

{% include "stack.c" %}

struct Thread;
typedef struct Thread Thread;
struct Thread {
  Stack stack;
  size_t program_counter;
};

void Thread_initialize(Thread* self, size_t program_counter) {
  Stack_initialize(&(self->stack));
  self->program_counter = program_counter;
}

void Thread_deinitialize(Thread* self) {
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

void drop(struct Thread* thread, const union Argument argument) {
  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));
  Object_deinitialize(&result);
}

void end(struct Thread* thread, const union Argument argument) {
}

void push(struct Thread* thread, const union Argument argument) {
  char* argumentString = argument.string;

  Object result;

  if(strcmp(argumentString, "print") == 0) {
    result.type = BUILTIN;
    result.value.builtin = PRINT;
  } else {
    assert(false);
  }

  Stack_push(&(thread->stack), result);
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
