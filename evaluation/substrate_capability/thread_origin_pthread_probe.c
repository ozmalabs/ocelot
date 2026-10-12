#define _GNU_SOURCE
#include <pthread.h>
#include <dlfcn.h>
#include <execinfo.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static int (*real_pthread_create)(pthread_t *, const pthread_attr_t *, void *(*)(void *), void *);
static __thread int in_probe;

int pthread_create(pthread_t *thread, const pthread_attr_t *attr,
                   void *(*start)(void *), void *arg) {
    if (!real_pthread_create) {
        real_pthread_create = dlsym(RTLD_NEXT, "pthread_create");
    }
    int result = real_pthread_create(thread, attr, start, arg);
    const char *path = getenv("OZMA_PTHREAD_LOG");
    if (result != 0 || !path || in_probe) return result;

    in_probe = 1;
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    long long ns = (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
    size_t stack_size = 0;
    if (attr) pthread_attr_getstacksize(attr, &stack_size);
    void *pcs[24];
    int count = backtrace(pcs, 24);
    int fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (fd >= 0) {
        char buf[8192];
        int used = snprintf(buf, sizeof(buf), "create\t%lld\t%ld\t%lu\t%zu\t%d",
                            ns, (long)syscall(SYS_gettid), (unsigned long)*thread,
                            stack_size, count);
        for (int i = 2; i < count && used < (int)sizeof(buf) - 128; ++i) {
            Dl_info info;
            memset(&info, 0, sizeof(info));
            dladdr(pcs[i], &info);
            uintptr_t base = (uintptr_t)info.dli_fbase;
            uintptr_t pc = (uintptr_t)pcs[i];
            used += snprintf(buf + used, sizeof(buf) - (size_t)used,
                             "\t%s!%s+0x%lx",
                             info.dli_fname ? info.dli_fname : "?",
                             info.dli_sname ? info.dli_sname : "?",
                             (unsigned long)(pc - base));
        }
        if (used < (int)sizeof(buf) - 1) buf[used++] = '\n';
        (void)write(fd, buf, (size_t)used);
        close(fd);
    }
    in_probe = 0;
    return result;
}
