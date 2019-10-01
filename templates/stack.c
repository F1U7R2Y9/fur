struct _StackNode;
typedef struct _StackNode _StackNode;
struct _StackNode {
  Object value;
  _StackNode* next;
};

struct Stack;
typedef struct Stack Stack;
struct Stack {
  _StackNode* top;
};

void Stack_initialize(Stack* self) {
  self->top = NULL;
}

bool Stack_isEmpty(Stack* self) {
  return self->top == NULL;
}

Object Stack_pop(Stack*);

void Stack_deinitialize(Stack* self) {
  while(self->top != NULL) {
    Object o = Stack_pop(self);
    Object_deinitialize(&o);
  }
}

void Stack_push(Stack* self, Object value) {
  _StackNode* node = malloc(sizeof(_StackNode));
  node->value = value;
  node->next = self->top;
  self->top = node;
}

Object Stack_pop(Stack* self) {
  assert(self->top != NULL);

  _StackNode* node = self->top;
  self->top = node->next;

  Object result = node->value;
  free(node);
  return result;
}
