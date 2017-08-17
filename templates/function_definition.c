
Object user${{name}}$implementation(EnvironmentPool* environmentPool, Environment* parent, size_t argc, Object* args)
{
  assert(argc == {{ argument_name_list|length }});

  Environment* environment = EnvironmentPool_allocate(environmentPool);
  Environment_initialize(environment, parent);
  Object result = builtin$nil;

  {% for argument_name in argument_name_list %}
  Environment_set(environment, "{{ argument_name }}", args[{{ loop.index0 }}]);
  {% endfor %}

  {% for statement in statement_list %}
  {{ statement }}
  {% endfor %}

  Environment_setLive(environment, false);
  return result;
}
