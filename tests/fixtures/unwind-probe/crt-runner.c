#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

static int counter;

static void verify_exit(void) {
    if (counter != 1) {
        fprintf(stderr, "DSO destructor count at exit: %d, expected 1\n", counter);
        _Exit(1);
    }
    puts("DSO finalization verified");
}

int main(int argc, char **argv) {
    if (argc != 2 || atexit(verify_exit) != 0) {
        return 1;
    }
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        _Exit(1);
    }
    void (*set_target)(int *) = (void (*)(int *))dlsym(handle, "set_target");
    if (!set_target) {
        fprintf(stderr, "missing set_target\n");
        _Exit(1);
    }
    set_target(&counter);
    if (dlclose(handle) != 0) {
        fprintf(stderr, "dlclose failed: %s\n", dlerror());
        _Exit(1);
    }
#ifdef __GLIBC__
    const int expected = 1;
#else
    /* В musl выгрузка DSO откладывается до завершения процесса. */
    const int expected = 0;
#endif
    if (counter != expected) {
        fprintf(stderr, "DSO destructor count after dlclose: %d, expected %d\n", counter, expected);
        _Exit(1);
    }
    return 0;
}
