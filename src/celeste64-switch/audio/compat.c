// Narrow, fail-fast Android ABI adapter for the FMOD compatibility layer.
#include "so_util.h"
#include <errno.h>
#include <fcntl.h>
#include <malloc.h>
#include <math.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <switch.h>
#include <time.h>
#include <unistd.h>
void c64_audio_log(const char *, ...);
int c64_loader_log(const char *fmt, ...) {
  char b[1024];
  va_list v;
  va_start(v, fmt);
  vsnprintf(b, sizeof(b), fmt, v);
  va_end(v);
  c64_audio_log("LOADER %s", b);
  return 0;
}
void c64_audio_fatal(const char *fmt, ...) {
  char b[1024];
  va_list v;
  va_start(v, fmt);
  vsnprintf(b, sizeof(b), fmt, v);
  va_end(v);
  c64_audio_log("C64_AUDIO FAIL %s", b);
  exit(20);
}
static void unsupported(const char *n) {
  c64_audio_fatal("unsupported Android call %s", n);
}
static uint64_t main_tls[128];
static void set_tls(void *p) { __asm__ volatile("msr tpidr_el0, %0" ::"r"(p)); }
static pthread_mutex_t adapter_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t *get_mutex(uintptr_t *slot) {
  pthread_mutex_lock(&adapter_lock);
  if (*slot <= 0xffff) {
    unsigned type = *slot;
    pthread_mutex_t *m = malloc(sizeof(*m));
    if (!m)
      c64_audio_fatal("mutex allocation");
    pthread_mutexattr_t at;
    pthread_mutexattr_init(&at);
    if (type & 0x4000)
      pthread_mutexattr_settype(&at, PTHREAD_MUTEX_RECURSIVE);
    else if (type & 0x8000)
      pthread_mutexattr_settype(&at, PTHREAD_MUTEX_ERRORCHECK);
    int rc = pthread_mutex_init(m, &at);
    pthread_mutexattr_destroy(&at);
    if (rc)
      c64_audio_fatal("mutex init %d", rc);
    *slot = (uintptr_t)m;
  }
  pthread_mutex_t *m = (void *)*slot;
  pthread_mutex_unlock(&adapter_lock);
  return m;
}
static int mutex_init(uintptr_t *p, const int *a) {
  *p = a && *a == 1 ? 0x4000 : a && *a == 2 ? 0x8000 : 0;
  get_mutex(p);
  return 0;
}
static int mutex_destroy(uintptr_t *p) {
  pthread_mutex_t *m = get_mutex(p);
  int r = pthread_mutex_destroy(m);
  if (!r) {
    free(m);
    *p = 0;
  }
  return r;
}
static int mutex_lock(uintptr_t *p) { return pthread_mutex_lock(get_mutex(p)); }
static int mutex_trylock(uintptr_t *p) {
  int r = pthread_mutex_trylock(get_mutex(p));
  return r == EBUSY ? 16 : r;
}
static int mutex_unlock(uintptr_t *p) {
  return pthread_mutex_unlock(get_mutex(p));
}
static int mattr_init(int *p) {
  *p = 0;
  return 0;
}
static int mattr_type(int *p, int t) {
  if (t > 2 || t < 0)
    return 22;
  *p = t;
  return 0;
}
static int mattr_destroy(int *p) { return 0; }
static int once(int *p, void (*fn)(void)) {
  int expected = 0;
  if (__atomic_compare_exchange_n(p, &expected, 1, 0, __ATOMIC_ACQ_REL,
                                  __ATOMIC_ACQUIRE)) {
    fn();
    __atomic_store_n(p, 2, __ATOMIC_RELEASE);
  } else
    while (__atomic_load_n(p, __ATOMIC_ACQUIRE) != 2)
      svcSleepThread(100000);
  return 0;
}
typedef struct {
  size_t stack;
  int detached;
} Attr;
static int attr_init(Attr *a) {
  a->stack = 256 * 1024;
  a->detached = 0;
  return 0;
}
static int attr_destroy(Attr *a) { return 0; }
static int attr_stack(Attr *a, size_t n) {
  a->stack = n;
  return 0;
}
static int attr_detach(Attr *a, int n) {
  if (n < 0 || n > 1)
    return 22;
  a->detached = n;
  return 0;
}
typedef struct {
  void *(*fn)(void *);
  void *arg;
} Start;
static void *thread_start(void *p) {
  Start start = *(Start *)p;
  free(p);
  uint64_t tls[128] = {0};
  set_tls(tls);
  u64 allowed = 0;
  if (R_SUCCEEDED(
          svcGetInfo(&allowed, InfoType_CoreMask, CUR_PROCESS_HANDLE, 0))) {
    u32 audio_cores = allowed & 6;
    if (audio_cores) {
      int ideal = (audio_cores & 2) ? 1 : 2;
      Result rc = svcSetThreadCoreMask(CUR_THREAD_HANDLE, ideal, audio_cores);
      c64_audio_log("C64_AUDIO worker core mask=%x result=%x", audio_cores, rc);
    }
  }
  return start.fn(start.arg);
}
static int create(uint64_t *out, const Attr *a, void *(*fn)(void *),
                  void *arg) {
  Start *s = malloc(sizeof(*s));
  if (!s)
    return 12;
  *s = (Start){fn, arg};
  pthread_attr_t at;
  pthread_attr_init(&at);
  pthread_attr_setstacksize(&at,
                            a && a->stack > 256 * 1024 ? a->stack : 256 * 1024);
  if (a && a->detached)
    pthread_attr_setdetachstate(&at, PTHREAD_CREATE_DETACHED);
  pthread_t t;
  int r = pthread_create(&t, &at, thread_start, s);
  pthread_attr_destroy(&at);
  if (r)
    free(s);
  else {
    *out = (uint64_t)t;
    c64_audio_log("C64_AUDIO thread created");
  }
  return r;
}
_Static_assert(sizeof(Semaphore) <= 16, "Bionic semaphore storage");
static int sem_init_bridge(Semaphore *s, int shared, unsigned n) {
  if (shared)
    unsupported("process shared semaphore");
  semaphoreInit(s, n);
  return 0;
}
static int sem_destroy_bridge(Semaphore *s) { return 0; }
static int sem_post_bridge(Semaphore *s) {
  semaphoreSignal(s);
  return 0;
}
static int sem_wait_bridge(Semaphore *s) {
  semaphoreWait(s);
  return 0;
}
static int android_log(int level, const char *tag, const char *message) {
  c64_audio_log("ANDROID %s: %s", tag, message);
  return 0;
}
static int *errno_bridge(void) { return &errno; }
static int gettid_bridge(void) {
  u64 id = 0;
  svcGetThreadId(&id, CUR_THREAD_HANDLE);
  return (int)id;
}
static int clock_bridge(int c, struct timespec *t) {
  if (c == 0)
    return clock_gettime(CLOCK_REALTIME, t);
  if (c == 1) {
    uint64_t n = armTicksToNs(armGetSystemTick());
    t->tv_sec = n / 1000000000;
    t->tv_nsec = n % 1000000000;
    return 0;
  }
  unsupported("clock id");
  return -1;
}
static int priority_bridge(int which, unsigned who, int priority) {
  c64_audio_log("C64_AUDIO priority request %d left at native default",
                priority);
  return 0;
}
static long syscall_bridge(long n, ...) {
  if (n == 178)
    return gettid_bridge();
  c64_audio_log("C64_AUDIO syscall %ld", n);
  unsupported("syscall");
  return -1;
}
static void *dlopen_bridge(const char *n, int flags) {
  c64_audio_log("C64_AUDIO dlopen %s", n ? n : "NULL");
  if (!n)
    return so_first();
  const char *b = strrchr(n, '/');
  return so_find_module(b ? b + 1 : n);
}
static void *dlsym_bridge(void *h, const char *n) {
  return (void *)(so_is_module(h) ? so_lookup_export(h, n)
                                  : so_lookup_export_all(n));
}
static int dlclose_bridge(void *h) { return 0; }
static char *dlerror_bridge(void) {
  return "library unavailable in FMOD integration";
}
static void assert_bridge(const char *f, int l, const char *fn, const char *e) {
  c64_audio_fatal("Android assert %s:%d %s %s", f, l, fn, e);
}
extern int __cxa_atexit(void (*)(void *), void *, void *);
extern void __cxa_finalize(void *);
extern int __cxa_guard_acquire(void *);
extern void __cxa_guard_release(void *);
extern void __cxa_pure_virtual(void);
static unsigned char fake_stdio[3][152];
static FILE *stdio_map(FILE *f) {
  uintptr_t offset = (uintptr_t)f - (uintptr_t)fake_stdio;
  if (offset < sizeof(fake_stdio)) {
    if (offset % 152)
      unsupported("stdio interior access");
    return offset == 0 ? stdin : offset == 152 ? stdout : stderr;
  }
  return f;
}
static int fprintf_bridge(FILE *f, const char *fmt, ...) {
  va_list v;
  va_start(v, fmt);
  int n = vfprintf(stdio_map(f), fmt, v);
  va_end(v);
  return n;
}
static size_t fwrite_bridge(const void *p, size_t a, size_t b, FILE *f) {
  return fwrite(p, a, b, stdio_map(f));
}
static int fflush_bridge(FILE *f) { return fflush(f ? stdio_map(f) : NULL); }
static int fclose_bridge(FILE *f) { return fclose(stdio_map(f)); }
static int open_bridge(const char *path, int flags, ...) {
  c64_audio_log("C64_AUDIO open %s flags=%x", path, flags);
  int f = flags & 3;
  if (flags & 0100)
    f |= O_CREAT;
  if (flags & 0200)
    f |= O_EXCL;
  if (flags & 01000)
    f |= O_TRUNC;
  if (flags & 02000)
    f |= O_APPEND;
  if (flags & 04000)
    f |= O_NONBLOCK;
  if (flags & ~(3 | 0100 | 0200 | 01000 | 02000 | 04000 | 02000000))
    unsupported("open flags");
  int mode = 0;
  if (flags & 0100) {
    va_list v;
    va_start(v, flags);
    mode = va_arg(v, int);
    va_end(v);
  }
  int fd = open(path, f, mode);
  c64_audio_log("C64_AUDIO open result=%d errno=%d", fd, fd < 0 ? errno : 0);
  return fd;
}
#include "imports.inc"
static Handle process_handle;
Handle c64ProcessHandle(void) { return process_handle; }
static void send_handle(void *arg) {
  Handle client = *(Handle *)arg;
  HipcRequest req =
      hipcMakeRequestInline(armGetTls(), .type = 4, .num_copy_handles = 1);
  req.copy_handles[0] = CUR_PROCESS_HANDLE;
  Result rc = svcSendSyncRequest(client);
  c64_audio_log("C64_AUDIO handle sender result=%x", rc);
}
static void acquire_process(void) {
  process_handle = envGetOwnProcessHandle();
  if (process_handle)
    return;
  Handle server, client;
  Result rc = svcCreateSession(&server, &client, false, 0);
  if (R_FAILED(rc))
    c64_audio_fatal("create local session %x", rc);
  Thread sender;
  rc = threadCreate(&sender, send_handle, &client, NULL, 0x10000, 0x2c, -2);
  if (R_FAILED(rc))
    c64_audio_fatal("create handle thread %x", rc);
  threadStart(&sender);
  s32 index;
  rc = svcReplyAndReceive(&index, &server, 1, INVALID_HANDLE, 1000000000LL);
  if (R_FAILED(rc))
    c64_audio_fatal("receive process handle %x", rc);
  HipcParsedRequest req = hipcParseRequest(armGetTls());
  if (req.meta.num_copy_handles != 1)
    c64_audio_fatal("no copied process handle");
  process_handle = req.data.copy_handles[0];
  svcCloseHandle(server);
  threadWaitForExit(&sender);
  threadClose(&sender);
  svcCloseHandle(client);
  c64_audio_log("C64_AUDIO acquired process handle=%x", process_handle);
}
void c64_android_load(void) {
  set_tls(main_tls);
  acquire_process();
  c64_audio_log("C64_AUDIO process handle=%x mapcode=%d", process_handle,
                envIsSyscallHinted(0x77));
  static so_module modules[2];
#ifdef C64_AUDIO_RELEASE
  const char *names[] = {"libfmod.so", "libfmodstudio.so"};
#else
  const char *names[] = {"libfmodL.so", "libfmodstudioL.so"};
#endif

  for (int i = 0; i < 2; i++) {
    char p[256];
    snprintf(p, sizeof(p), "sdmc:/switch/celeste64/fmod/%s", names[i]);
    void *base = memalign(4096, 8 * 1024 * 1024);
    if (!base)
      c64_audio_fatal("load allocation");
    int r = so_load(&modules[i], p, base, 8 * 1024 * 1024);
    if (r)
      c64_audio_fatal("load %s %d", p, r);
    so_relocate(&modules[i]);
  }
  for (int i = 0; i < 2; i++)
    if (so_resolve(&modules[i], imports, sizeof(imports) / sizeof(imports[0]),
                   0))
      c64_audio_fatal("unresolved imports");
  for (int i = 0; i < 2; i++) {
    so_finalize(&modules[i]);
    so_flush_caches(&modules[i]);
  }
  for (int i = 0; i < 2; i++) {
    c64_audio_log("C64_AUDIO constructors %s", names[i]);
    so_execute_init_array(&modules[i]);
  }
  c64_audio_log("C64_AUDIO libraries loaded");
  extern void c64_jni_init(void);
  c64_jni_init();
}
