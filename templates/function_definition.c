
Object user${{name}}$implementation(EnvironmentPool* environmentPool, Environment* environment, size_t argc, Stack* parentStack, jmp_buf parentJump)
{
  environment = Environment_construct(environmentPool, environment);

  Stack* stack = Stack_construct();
  StackSnapshot stackSnapshot = Stack_takeSnapshot(stack);

  jmp_buf jump;
  if(setjmp(jump) != 0)
  {
    fprintf(stderr, "\tin {{name}}\n");

    Stack_rewind(stack, stackSnapshot);
    Environment_setLive(environment, false);

    Stack_destruct(stack);

    longjmp(parentJump, 1);
  }

  Object result = builtin$nil;

  {% for argument_name in argument_name_list|reverse %}
  Environment_set(environment, "{{ argument_name }}", Stack_pop(parentStack));
  {% endfor %}

  {% for statement in statement_list %}
  {{ statement }}
  {% endfor %}

  // TODO Set the environment back to the parent environment
  Environment_setLive(environment, false);

  Stack_destruct(stack);
  return result;
}
