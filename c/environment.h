#ifndef ENVIRONMENT_H
#define ENVIRONMENT_H

#include <stdbool.h>
#include "symbol.h"
#include "object.h"

struct Environment;
typedef struct Environment Environment;

Environment* Environment_create(Environment*);

struct EnvironmentGetResult;
typedef struct EnvironmentGetResult EnvironmentGetResult;
struct EnvironmentGetResult {
  bool found;
  Object* value;
};

EnvironmentGetResult Environment_get(Environment*, Symbol*);
bool Environment_set(Environment*, Symbol*, Object*);

#endif
