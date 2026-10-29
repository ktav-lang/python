/* Очистка ELF DSO: https://itanium-cxx-abi.github.io/cxx-abi/abi.html#dso-dtor */
__attribute__((visibility("hidden"))) void *__dso_handle = &__dso_handle;

extern void __cxa_finalize(void *) __attribute__((weak));

__attribute__((destructor)) static void finalize_dso(void) {
    if (__cxa_finalize) {
        __cxa_finalize(&__dso_handle);
    }
}
