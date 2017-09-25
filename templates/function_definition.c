
Object user${{name}}$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Stack* parentStack, jmp_buf parentJump)
{
  Environment* environment = EnvironmentPool_allocate(environmentPool);
  Environment_initialize(environment, parent);

  Stack stackMemory;
  Stack* stack = &stackMemory;
  Stack_initialize(stack);

  jmp_buf jump;
  if(setjmp(jump) != 0)
  {
    fprintf(stderr, "\tin {{name}}\n");

    while(Stack_any(stack))
    {
      Object item = Stack_pop(stack);
      Object_deinitialize(&item);
    }
    Environment_setLive(environment, false);

    longjmp(parentJump, 1);
  }

  Object result = builtin$nil;

  {% for argument_name in argument_name_list|reverse %}
  Environment_set(environment, "{{ argument_name }}", Stack_pop(parentStack));
  {% endfor %}

  {% for statement in statement_list %}
  {{ statement }}
  {% endfor %}

  Environment_setLive(environment, false);
  return result;
}
