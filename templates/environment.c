struct _EnvironmentNode;
typedef struct _EnvironmentNode _EnvironmentNode;
struct _EnvironmentNode {
  const char* symbol;
  Object value;
  _EnvironmentNode* next;
};

struct Environment;
typedef struct Environment Environment;
struct Environment {
  _EnvironmentNode* top;
};

struct Environment_get_Result;
typedef struct Environment_get_Result Environment_get_Result;
struct Environment_get_Result {
  bool found;
  Object result;
};

void Environment_initialize(Environment* self) {
  self->top = NULL;
}

void Environment_deinitialize(Environment* self) {
  while(self->top != NULL) {
    _EnvironmentNode* en = self->top;
    self->top = en->next;
    Object_deinitialize(&(en->value));
    free(en);
  }
}

Environment* Environment_construct() {
  Environment* result = malloc(sizeof(Environment));
  Environment_initialize(result);
  return result;
}

void Environment_destruct(Environment* self) {
  Environment_deinitialize(self);
  free(self);
}

Environment_get_Result Environment_get(Environment* self, char* symbol) {
  for(_EnvironmentNode* current = self->top; current != NULL; current = current->next) {
    if(strcmp(current->symbol, symbol) == 0) {
      return (Environment_get_Result) { true, current->value };
    }
  }
  return (Environment_get_Result) { false, BUILTIN_NIL };
}

void Environment_set(Environment* self, char* symbol, Object value) {
  assert(!(Environment_get(self, symbol).found));

  _EnvironmentNode* en = malloc(sizeof(_EnvironmentNode));
  en->symbol = symbol;
  en->value = value;
  en->next = self->top;
  self->top = en;
}
