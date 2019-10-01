struct _EnvironmentNode;
typedef struct _EnvironmentNode _EnvironmentNode;
struct _EnvironmentNode {
  const char* symbol;
  Object value;
  _EnvironmentNode* next;
};

struct Environment {
  size_t referenceCount;
  Environment* shadowed;
  _EnvironmentNode* top;
};

struct Environment_get_Result;
typedef struct Environment_get_Result Environment_get_Result;
struct Environment_get_Result {
  bool found;
  Object result;
};

void Environment_initialize(Environment* self, Environment* shadowed) {
  self->referenceCount = 1;
  self->shadowed = shadowed;
  self->top = NULL;
}

void Environment_deinitialize(Environment* self) {
  assert(self->referenceCount == 0);

  while(self->top != NULL) {
    _EnvironmentNode* en = self->top;
    self->top = en->next;
    Object_deinitialize(&(en->value));
    free(en);
  }
}

Environment* Environment_construct(Environment* shadowed) {
  Environment* result = malloc(sizeof(Environment));
  Environment_initialize(result, shadowed);
  return result;
}

Environment* Environment_reference(Environment* self) {
  self->referenceCount++; // TODO Do we need to make this thread safe?
  return self;
}

void Environment_destruct(Environment* self) {
  self->referenceCount--; // TODO Do we need to make this thread safe?
  if(self->referenceCount == 0) {
    Environment_deinitialize(self);
    free(self);
  }
}

Environment_get_Result Environment_getShallow(Environment* self, char* symbol) {
  for(_EnvironmentNode* current = self->top; current != NULL; current = current->next) {
    if(strcmp(current->symbol, symbol) == 0) {
      return (Environment_get_Result) { true, current->value };
    }
  }
  return (Environment_get_Result) { false, BUILTIN_NIL };
}

Environment_get_Result Environment_get(Environment* self, char* symbol) {
  for(; self != NULL; self = self->shadowed) {
    Environment_get_Result result = Environment_getShallow(self, symbol);
    if(result.found) return result;
  }
  return (Environment_get_Result) { false, BUILTIN_NIL };
}

void Environment_set(Environment* self, char* symbol, Object value) {
  assert(!(Environment_getShallow(self, symbol).found));

  _EnvironmentNode* en = malloc(sizeof(_EnvironmentNode));
  en->symbol = symbol;
  en->value = value;
  en->next = self->top;
  self->top = en;
}
