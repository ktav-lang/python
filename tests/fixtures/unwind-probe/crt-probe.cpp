static int *counter;

struct Cleanup {
    ~Cleanup() {
        if (counter) {
            ++*counter;
        }
    }
};

static Cleanup cleanup;

extern "C" __attribute__((visibility("default"))) void set_target(int *target) {
    counter = target;
}
