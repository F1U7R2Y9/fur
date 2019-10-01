#include<assert.h>
#include<stdbool.h>
#include<stdint.h>
#include<stdio.h>
#include<stdlib.h>
#include<string.h>

enum Type;
typedef enum Type Type;
enum Type {
  BOOLEAN,
  BUILTIN,
  CLOSURE,
  INTEGER,
  STRING
};

enum Builtin;
typedef enum Builtin Builtin;
enum Builtin {
  NIL,
  POW,
  PRINT
};

struct Object;
typedef struct Object Object;
struct Environment;
typedef struct Environment Environment;
struct Thread;
typedef struct Thread Thread;

struct Closure;
typedef struct Closure Closure;
struct Closure {
  Environment* environment;
  size_t entry;
};

union Value;
typedef union Value Value;
union Value {
  Builtin builtin;
  Closure closure;
  bool boolean;
  char* string;
  int32_t integer;
};

struct Object {
  Type type;
  Value value;
};

#define BUILTIN_NIL (Object) { BUILTIN, (Value)(Builtin)NIL }

void Object_deinitialize(Object* self) {
}

{% include "environment.c" %}
{% include "stack.c" %}
{% include "frame.c" %}

struct Thread {
  Frame frame;
  Stack stack;
};

void Thread_initialize(Thread* self, size_t programCounter) {
  Frame_initialize(&(self->frame), Environment_construct(NULL), NULL, programCounter);
  Stack_initialize(&(self->stack));
}

void Thread_deinitialize(Thread* self) {
  Frame_deinitialize(&(self->frame));
  Stack_deinitialize(&(self->stack));
}

Environment* Thread_getEnvironment(Thread* self) {
  return self->frame.environment;
}

void Thread_setProgramCounter(Thread* self, size_t programCounter) {
  self->frame.programCounter = programCounter;
}

void Thread_incrementProgramCounter(Thread* self) {
  self->frame.programCounter++;
}

size_t Thread_getProgramCounter(Thread* self) {
  return self->frame.programCounter;
}

union Argument;
typedef const union Argument Argument;
union Argument {
  size_t label;
  void* pointer;
  char* string;
  int32_t integer;
};

void callBuiltinPow(Thread* thread, size_t argumentCount) {
  assert(argumentCount == 2);
  assert(!Stack_isEmpty(&(thread->stack)));
  Object exponent = Stack_pop(&(thread->stack));
  assert(exponent.type == INTEGER);
  assert(exponent.value.integer >= 0);

  assert(!Stack_isEmpty(&(thread->stack)));
  Object base = Stack_pop(&(thread->stack));
  assert(base.type == INTEGER);

  Object result;
  result.type = INTEGER;
  result.value.integer = 1;

  while(exponent.value.integer > 0) {
    result.value.integer *= base.value.integer;
    exponent.value.integer--;
  }

  Stack_push(&(thread->stack), result);
}

void callBuiltinPrint(Thread* thread, size_t argumentCount) {
  assert(argumentCount > 0);

  Object arguments[argumentCount];
  size_t count;

  for(count = 0; count < argumentCount; count++) {
    assert(!Stack_isEmpty(&(thread->stack)));
    arguments[argumentCount - count - 1] = Stack_pop(&(thread->stack));
  }

  for(count = 0; count < argumentCount; count ++) {
    Object arg = arguments[count];

    switch(arg.type) {
      case BOOLEAN:
        if(arg.value.boolean) printf("true");
        else printf("false");
        break;

      case INTEGER:
        printf("%i", arg.value.integer);
        break;

      case STRING:
        printf("%s", arg.value.string);
        break;

      default:
        assert(false);
    }
  }

  Stack_push(&(thread->stack), BUILTIN_NIL);
}

void callBuiltin(Thread* thread, Builtin b, size_t argumentCount) {
  switch(b) {
    case POW:
      callBuiltinPow(thread, argumentCount);
      break;
    case PRINT:
      callBuiltinPrint(thread, argumentCount);
      break;

    default:
      assert(false);
  }
}

void callClosure(Thread* thread, Closure closure, size_t argumentCount) {
  assert(argumentCount == 0);

  Frame* returnFrame = malloc(sizeof(Frame));
  *returnFrame = thread->frame;
  Frame_initialize(
    &(thread->frame),
    Environment_construct(Environment_reference(closure.environment)),
    returnFrame,
    closure.entry - 1 // We will increment the frame immediately after this
  );
}

void inst_call(Thread* thread, Argument argument) {
  assert(!Stack_isEmpty(&(thread->stack)));
  Object f = Stack_pop(&(thread->stack));
  size_t argumentCount = argument.label;

  switch(f.type) {
    case BUILTIN:
      callBuiltin(thread, f.value.builtin, argumentCount);
      break;

    case CLOSURE:
      callClosure(thread, f.value.closure, argumentCount);
      break;

    default:
      assert(false);
  }
}

{% with name='add', operation='+' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

void inst_close(Thread* thread, Argument argument) {
  Object result;
  result.type = CLOSURE;
  result.value.closure.environment = Thread_getEnvironment(thread);
  result.value.closure.entry = argument.label;

  Stack_push(&(thread->stack), result);
}

void inst_drop(Thread* thread, Argument argument) {
  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));
  Object_deinitialize(&result);
}

void inst_end(Thread* thread, Argument argument) {
}

{% with name='eq', operation='==' %}
  {% include "comparison_instruction.c" %}
{% endwith %}

{% with name='gt', operation='>' %}
  {% include "comparison_instruction.c" %}
{% endwith %}

{% with name='gte', operation='>=' %}
  {% include "comparison_instruction.c" %}
{% endwith %}

{% with name='idiv', operation='/' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

void inst_jump(Thread* thread, Argument argument) {
  Thread_setProgramCounter(thread, argument.label - 1); // We will increment before running
}

void inst_jump_if_false(Thread* thread, Argument argument) {
  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));
  assert(result.type == BOOLEAN);

  if(!(result.value.boolean)) {
    inst_jump(thread, argument);
  }
}

{% with name='lt', operation='<' %}
  {% include "comparison_instruction.c" %}
{% endwith %}

{% with name='lte', operation='<=' %}
  {% include "comparison_instruction.c" %}
{% endwith %}

{% with name='mod', operation='%' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

{% with name='mul', operation='*' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

{% with name='neq', operation='!=' %}
  {% include "comparison_instruction.c" %}
{% endwith %}

void inst_neg(Thread* thread, Argument argument) {
  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));
  assert(result.type == INTEGER);

  result.value.integer = -(result.value.integer);

  Stack_push(&(thread->stack), result);
}

void inst_pop(Thread* thread, Argument argument) {
  char* argumentString = argument.string;

  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));

  if(strcmp(argumentString, "print") == 0) {
    assert(false);
  } else if(strcmp(argumentString, "pow") == 0) {
    assert(false);
  }


  Environment_set(Thread_getEnvironment(thread), argumentString, result);
}

void inst_push(Thread* thread, Argument argument) {
  char* argumentString = argument.string;

  if(strcmp(argumentString, "false") == 0) {
    Stack_push(&(thread->stack), (Object){ BOOLEAN, false });
  }else if(strcmp(argumentString, "pow") == 0) {
    Object result;
    result.type = BUILTIN;
    result.value.builtin = POW;
    Stack_push(&(thread->stack), result);
  } else if(strcmp(argumentString, "print") == 0) {
    Object result;
    result.type = BUILTIN;
    result.value.builtin = PRINT;
    Stack_push(&(thread->stack), result);
  } else if(strcmp(argumentString, "true") == 0) {
    Stack_push(&(thread->stack), (Object){ BOOLEAN, true });
  } else {
    Environment_get_Result result = Environment_get(
      Thread_getEnvironment(thread),
      argumentString
    );
    if(!result.found) {
      fprintf(stderr, "Variable `%s` not found", argumentString);
      assert(false);
    }
    Stack_push(&(thread->stack), result.result);
  }
}

void inst_push_integer(Thread* thread, Argument argument) {
  Object result;
  result.type = INTEGER;
  result.value.integer = argument.integer;

  Stack_push(&(thread->stack), result);
}

void inst_push_string(Thread* thread, Argument argument) {
  Object result;
  result.type = STRING;
  result.value.string = argument.string;

  Stack_push(&(thread->stack), result);
}

{% with name='sub', operation='-' %}
  {% include "arithmetic_instruction.c" %}
{% endwith %}

void inst_return(Thread* thread, Argument argument) {
  Frame* returnFrame = thread->frame.returnFrame;

  Frame_deinitialize(&(thread->frame));

  Frame_initialize(
    &(thread->frame),
    returnFrame->environment,
    returnFrame->returnFrame,
    returnFrame->programCounter
  );

  free(returnFrame);
}

struct Instruction;
typedef const struct Instruction Instruction;
struct Instruction {
  void (*instruction)(Thread*,Argument);
  Argument argument;
};

{% for label in labels_to_instruction_indices.keys() %}
#define LABEL_{{ label }} {{ labels_to_instruction_indices[label] }}
{% endfor %}

const Instruction program[] = {
{% for instruction in instruction_list %}
  (Instruction){ inst_{{ instruction.instruction }}, (Argument){{ generate_argument(instruction) }} },
{% endfor %}
};

int main() {
  Thread thread;
  Thread_initialize(&thread, LABEL___main__);

  for(; program[Thread_getProgramCounter(&thread)].instruction != inst_end; Thread_incrementProgramCounter(&thread)) {
    program[Thread_getProgramCounter(&thread)].instruction(
      &thread,
      program[Thread_getProgramCounter(&thread)].argument
    );
  }

  Thread_deinitialize(&thread);

  return 0;
}
