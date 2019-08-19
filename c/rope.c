#ifndef ROPE_C
#define ROPE_C

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

enum RopeType;
typedef enum RopeType RopeType;
enum RopeType {
  ROPETYPE_CONCATENATION,
  ROPETYPE_STRING
};

struct Concatenation;
typedef struct Concatenation Concatenation;
struct Concatenation {
  Rope* r0;
  Rope* r1;
};

struct String;
typedef struct String String;
struct String {
  size_t length;
  uint32_t* characters;
};

union RopeInstance;
typedef union RopeInstance RopeInstance;
union RopeInstance {
  Concatenation concatenation;
  String string;
};

struct Rope {
  volatile size_t referenceCount;
  RopeType type;
  RopeInstance instance;
};

Rope* Rope_rereference(Rope* self) {
  __sync_add_and_fetch(&(self->referenceCount), 1);
  return self;
}

void Rope_destruct(Rope* self) {
  size_t referenceCount = __sync_sub_and_fetch(&(self->referenceCount), 1);

  if(referenceCount == 0) {
    switch(self->type) {
      case ROPETYPE_CONCATENATION:
        Rope_destruct(self->instance.concatenation.r0);
        Rope_destruct(self->instance.concatenation.r1);
        break;

      case ROPETYPE_STRING:
        free(self->instance.string.characters);
        break;

      default:
        assert(false);
    }

    free(self);
  }
}

void Rope_write(Rope*, Encoding, FILE) {
  // TODO Implement
  printf("Not implemented");
}

Rope* Rope_read(Encoding, FILE) {
  // TODO Implement
  printf("Not implemented");
  return NULL;
}

Rope* Rope_concatenate(Rope* r0, Rope* r1) {
  Rope* result = malloc(sizeof(Rope));
  result->referenceCount = 0;
  result->type = ROPETYPE_CONCATENATION;
  result->instance.concatenation.r0 = Rope_rereference(r0);
  result->instance.concatenation.r1 = Rope_rereference(r1);
  return result;
}

#endif
