#ifndef ENVIRONMENT_C
#define ENVIRONMENT_C

#include<assert.h>

struct EnvironmentNode;
typedef struct EnvironmentNode EnvironmentNode;
struct EnvironmentNode {
  Symbol* key;
  Object* value;
  EnvironmentNode* next;
};

struct Environment {
  Environment* parent;
  EnvironmentNode* root;
};

Environment* Environment_create(Environment* parent) {
  Environment* result = malloc(sizeof(Environment));
  result->parent = parent;
  result->root = NULL;
  return result;
}

EnvironmentGetResult Environment_get(Environment* self, Symbol* key) {
  if(self == NULL) return (EnvironmentGetResult) { false, NULL };

  for(EnvironmentNode* search = self->root; search != NULL; search = search->next) {
    if(search->key == key) return (EnvironmentGetResult) { true, search->value };
  }

  return Environment_get(self->parent, key);
}

bool Environment_set(Environment* self, Symbol* key, Object* value) {
  assert(self != NULL);

  for(EnvironmentNode* search = self->root; search != NULL; search = search->next) {
    if(search->key == key) return false;
  }

  EnvironmentNode* node = malloc(sizeof(EnvironmentNode));
  node->key = key;
  node->value = value;
  node->next = self->root;
  self->root = node;
  return true;
}

#endif
