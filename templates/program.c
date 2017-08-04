{% for standard_library in standard_libraries %}
#include<{{standard_library}}>
{% endfor %}

{% if 'print' in builtins %}
void builtin$print(const char* output)
{
  printf("%s", output);
}
{% endif %}

int main(int argc, char** argv)
{
  {% for statement in statements %}
  {{ statement }}
  {% endfor %}
  return 0;
}
