
Object user${{name}}$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Stack* stack, jmp_buf parent_jump)
{
  Environment* environment = EnvironmentPool_allocate(environmentPool);
  Environment_initialize(environment, parent);

  jmp_buf jump;
  if(setjmp(jump) != 0)
  {
    Environment_setLive(environment, false);
    fprintf(stderr, "Error in {{name}}\n");
    longjmp(parent_jump, 1);
  }

  Object result = builtin$nil;

  {% for argument_name in argument_name_list|reverse %}
  Environment_set(environment, "{{ argument_name }}", Stack_pop(stack));
  {% endfor %}

  {% for statement in statement_list %}
  {{ statement }}
  {% endfor %}

  Environment_setLive(environment, false);
  return result;
}
