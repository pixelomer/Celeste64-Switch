// Native FMOD boundary: no managed callbacks on FMOD threads.
#include "fmod.h"
#include "fmod_output.h"
#include "fmod_studio.h"
#include "so_util.h"
#include <malloc.h>
#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <switch.h>
void c64_android_load(void);
static Mutex log_lock;
void c64_audio_log(const char *fmt, ...) {
  char text[1024];
  va_list a;
  va_start(a, fmt);
  vsnprintf(text, sizeof(text), fmt, a);
  va_end(a);
  mutexLock(&log_lock);
  svcOutputDebugString(text, strlen(text));
  mutexUnlock(&log_lock);
}
#define APIS(X)                                                                  \
  X(FMOD_Studio_System_Create)                                                   \
  X(FMOD_Studio_System_GetCoreSystem)                                            \
  X(FMOD_System_GetVersion)                                                      \
  X(FMOD_Studio_System_Initialize) X(FMOD_Studio_System_Release) X(              \
      FMOD_Studio_System_Update) X(FMOD_System_RegisterOutput)                   \
      X(FMOD_System_SetOutputByPlugin) X(FMOD_System_SetSoftwareFormat) X(       \
          FMOD_System_SetDSPBufferSize) X(FMOD_Studio_System_LoadBankFile)       \
          X(FMOD_Studio_System_UnloadAll) X(                                     \
              FMOD_Studio_System_FlushCommands) X(FMOD_Studio_System_GetEvent)   \
              X(FMOD_Studio_EventDescription_CreateInstance) X(                  \
                  FMOD_Studio_EventInstance_SetCallback)                         \
                  X(FMOD_Studio_EventInstance_Start) X(                          \
                      FMOD_Studio_EventInstance_Stop)                            \
                      X(FMOD_Studio_EventInstance_Release) X(                    \
                          FMOD_Studio_EventInstance_GetPlaybackState)            \
                          X(FMOD_Studio_EventInstance_Get3DAttributes) X(        \
                              FMOD_Studio_EventInstance_Set3DAttributes)         \
                              X(FMOD_Studio_EventInstance_SetParameterByName) X( \
                                  FMOD_Studio_EventInstance_GetVolume)           \
                                  X(FMOD_Studio_EventInstance_SetVolume) X(      \
                                      FMOD_Studio_System_SetListenerAttributes)  \
                                      X(FMOD_Studio_System_GetBus)               \
                                          X(FMOD_Studio_System_GetVCA) X(        \
                                              FMOD_Studio_Bus_StopAllEvents)     \
                                              X(FMOD_Studio_Bus_SetPaused)       \
                                                  X(FMOD_Studio_VCA_SetVolume)
#define DECL(n) static __typeof__(&n) p_##n;
APIS(DECL)
#define LOAD(n)                                                                \
  p_##n = (__typeof__(&n))so_lookup_export_all(#n);                            \
  if (!p_##n) {                                                                \
    c64_audio_log("C64_AUDIO missing export " #n);                             \
    return -1;                                                                 \
  }
#define TRY(expr)                                                              \
  do {                                                                         \
    int result = (expr);                                                       \
    if (result) {                                                              \
      c64_audio_log("C64_AUDIO error %d: %s", result, #expr);                  \
      return result;                                                           \
    }                                                                          \
  } while (0)
static FMOD_STUDIO_SYSTEM *studio;
static int loaded;
#define BLOCK 512
#define BUFFERS 4
static AudioOutBuffer audio_buffers[BUFFERS];
static int in_flight[BUFFERS];
static unsigned next_buffer;
static float mix_buffer[BLOCK * 2];
static uint64_t deadline;
static uint64_t mix_count, marker_count, play_count, nonzero_blocks;
static uint64_t last_stats;
static int output_error;
static int stopping;
static Mutex marker_lock;
static FMOD_STUDIO_EVENTINSTANCE *marker_queue[256];
static unsigned marker_read, marker_write;
static FMOD_RESULT F_CALLBACK on_marker(FMOD_STUDIO_EVENT_CALLBACK_TYPE type,
                                        FMOD_STUDIO_EVENTINSTANCE *event,
                                        void *data) {
  if (type != FMOD_STUDIO_EVENT_CALLBACK_TIMELINE_MARKER)
    return FMOD_OK;
  mutexLock(&marker_lock);
  if (marker_write - marker_read < 256)
    marker_queue[marker_write++ % 256] = event;
  else
    c64_audio_log("C64_AUDIO marker overflow");
  marker_count++;
  mutexUnlock(&marker_lock);
  return FMOD_OK;
}
uintptr_t C64AudioMarker(void) {
  mutexLock(&marker_lock);
  uintptr_t r = marker_read == marker_write
                    ? 0
                    : (uintptr_t)marker_queue[marker_read++ % 256];
  mutexUnlock(&marker_lock);
  return r;
}
static FMOD_RESULT F_CALLBACK drivers(FMOD_OUTPUT_STATE *s, int *n) {
  *n = 1;
  return FMOD_OK;
}
static FMOD_RESULT F_CALLBACK driverinfo(FMOD_OUTPUT_STATE *s, int id, char *n,
                                         int len, FMOD_GUID *g, int *r,
                                         FMOD_SPEAKERMODE *m, int *c) {
  snprintf(n, len, "Switch audio");
  memset(g, 0, sizeof(*g));
  *r = 48000;
  *m = FMOD_SPEAKERMODE_STEREO;
  *c = 2;
  return FMOD_OK;
}
static FMOD_RESULT F_CALLBACK output_init(FMOD_OUTPUT_STATE *s, int d,
                                          FMOD_INITFLAGS fl, int *r,
                                          FMOD_SPEAKERMODE *m, int *c,
                                          FMOD_SOUND_FORMAT *f, int block,
                                          int *nb, int *extra, void *user) {
  *r = 48000;
  *m = FMOD_SPEAKERMODE_STEREO;
  *c = 2;
  *f = FMOD_SOUND_FORMAT_PCMFLOAT;
  *extra = 0;
  Result rc = audoutInitialize();
  if (R_FAILED(rc)) {
    c64_audio_log("C64_AUDIO audout init %x", rc);
    return FMOD_ERR_OUTPUT_INIT;
  }
  for (int i = 0; i < BUFFERS; i++) {
    void *p = memalign(4096, 4096);
    if (!p)
      return FMOD_ERR_MEMORY;
    audio_buffers[i] =
        (AudioOutBuffer){.buffer = p,
                         .buffer_size = 4096,
                         .data_size = BLOCK * 2 * sizeof(int16_t)};
    in_flight[i] = 0;
  }
  stopping = 0;
  deadline = 0;
  next_buffer = 0;
  output_error = 0;
  return FMOD_OK;
}
static FMOD_RESULT F_CALLBACK output_start(FMOD_OUTPUT_STATE *s) {
  return R_SUCCEEDED(audoutStartAudioOut()) ? FMOD_OK : FMOD_ERR_OUTPUT_INIT;
}
static FMOD_RESULT F_CALLBACK output_stop(FMOD_OUTPUT_STATE *s) {
  __atomic_store_n(&stopping, 1, __ATOMIC_RELEASE);
  audoutStopAudioOut();
  return FMOD_OK;
}
static FMOD_RESULT F_CALLBACK output_close(FMOD_OUTPUT_STATE *s) {
  audoutExit();
  for (int i = 0; i < BUFFERS; i++) {
    free(audio_buffers[i].buffer);
    audio_buffers[i].buffer = NULL;
  }
  return FMOD_OK;
}
static FMOD_RESULT F_CALLBACK output_mix(FMOD_OUTPUT_STATE *s) {
  if (__atomic_load_n(&stopping, __ATOMIC_ACQUIRE))
    return FMOD_OK;
  // Explicit cadence also handles emulators that release buffers immediately.
  uint64_t now = armTicksToNs(armGetSystemTick());
  if (!deadline || now > deadline + 100000000ULL)
    deadline = now - (BUFFERS - 1) * BLOCK * 1000000000ULL / 48000;
  if (now < deadline)
    svcSleepThread(deadline - now);
  deadline += BLOCK * 1000000000ULL / 48000;
  unsigned slot = next_buffer % BUFFERS;
  while (in_flight[slot]) {
    AudioOutBuffer *released = NULL;
    u32 n = 0;
    Result rc = audoutWaitPlayFinish(&released, &n, 200000000ULL);
    if (__atomic_load_n(&stopping, __ATOMIC_ACQUIRE))
      return FMOD_OK;
    if (R_FAILED(rc)) {
      __atomic_store_n(&output_error, (int)rc, __ATOMIC_RELAXED);
      return FMOD_ERR_OUTPUT_DRIVERCALL;
    }
    if (n) {
      for (int i = 0; i < BUFFERS; i++)
        if (released == &audio_buffers[i])
          in_flight[i] = 0;
    }
  }
  FMOD_RESULT r = s->readfrommixer(s, mix_buffer, BLOCK);
  if (r) {
    __atomic_store_n(&output_error, (int)r, __ATOMIC_RELAXED);
    return r;
  }
  int16_t *pcm = audio_buffers[slot].buffer;
  int nonzero = 0;
  for (int i = 0; i < BLOCK * 2; i++) {
    if (!isfinite(mix_buffer[i])) {
      __atomic_store_n(&output_error, -2, __ATOMIC_RELAXED);
      return FMOD_ERR_INTERNAL;
    }
    if (fabsf(mix_buffer[i]) > 0.00001f)
      nonzero = 1;
  }
  if (nonzero)
    __atomic_fetch_add(&nonzero_blocks, 1, __ATOMIC_RELAXED);
  for (int i = 0; i < BLOCK * 2; i++)
    pcm[i] = (int16_t)(fmaxf(-1, fminf(1, mix_buffer[i])) * 32767);
  armDCacheFlush(pcm, BLOCK * 2 * sizeof(int16_t));
  Result rc = audoutAppendAudioOutBuffer(&audio_buffers[slot]);
  if (R_FAILED(rc)) {
    __atomic_store_n(&output_error, (int)rc, __ATOMIC_RELAXED);
    return FMOD_ERR_OUTPUT_DRIVERCALL;
  }
  in_flight[slot] = 1;
  next_buffer++;
  __atomic_fetch_add(&mix_count, 1, __ATOMIC_RELAXED);
  return FMOD_OK;
}
static FMOD_OUTPUT_DESCRIPTION output = {
    .apiversion = FMOD_OUTPUT_PLUGIN_VERSION,
    .name = "libnx audio",
    .version = 1,
    .method = FMOD_OUTPUT_METHOD_MIX_DIRECT,
    .getnumdrivers = drivers,
    .getdriverinfo = driverinfo,
    .init = output_init,
    .start = output_start,
    .stop = output_stop,
    .close = output_close,
    .mixer = output_mix};
int C64AudioInit(void) {
  if (studio)
    return 0;
  if (!loaded) {
    const char *files[] = {"sdmc:/switch/celeste64/fmod/libfmod.so",
                           "sdmc:/switch/celeste64/fmod/libfmodstudio.so"};
    for (int i = 0; i < 2; i++) {
      FILE *f = fopen(files[i], "rb");
      if (!f) {
        c64_audio_log("C64_AUDIO missing %s", files[i]);
        return -1;
      }
      fclose(f);
    }
    c64_android_load();
    loaded = 1;
    APIS(LOAD)
  }
  TRY(p_FMOD_Studio_System_Create(&studio, FMOD_VERSION));
  FMOD_SYSTEM *core;
  unsigned version, plugin;
  TRY(p_FMOD_Studio_System_GetCoreSystem(studio, &core));
  TRY(p_FMOD_System_GetVersion(core, &version));
  TRY(p_FMOD_System_RegisterOutput(core, &output, &plugin));
  TRY(p_FMOD_System_SetOutputByPlugin(core, plugin));
  TRY(p_FMOD_System_SetSoftwareFormat(core, 48000, FMOD_SPEAKERMODE_STEREO, 0));
  TRY(p_FMOD_System_SetDSPBufferSize(core, BLOCK, BUFFERS));
  TRY(p_FMOD_Studio_System_Initialize(studio, 1024, FMOD_STUDIO_INIT_NORMAL,
                                      FMOD_INIT_NORMAL, NULL));
  c64_audio_log("C64_AUDIO ready FMOD=%x rate=48000 block=%d buffers=%d",
                version, BLOCK, BUFFERS);
  return 0;
}
int C64AudioUpdate(void) {
  if (!studio)
    return 0;
  int e = __atomic_load_n(&output_error, __ATOMIC_RELAXED);
  if (e)
    return e;
  uint64_t now = armTicksToNs(armGetSystemTick());
  if (now - last_stats > 10000000000ULL) {
    last_stats = now;
    mutexLock(&marker_lock);
    uint64_t marks = marker_count;
    mutexUnlock(&marker_lock);
    c64_audio_log(
        "C64_AUDIO stats blocks=%llu nonzero=%llu plays=%llu markers=%llu",
        (unsigned long long)__atomic_load_n(&mix_count, __ATOMIC_RELAXED),
        (unsigned long long)__atomic_load_n(&nonzero_blocks, __ATOMIC_RELAXED),
        (unsigned long long)play_count, (unsigned long long)marks);
  }
  return p_FMOD_Studio_System_Update(studio);
}
int C64AudioLoad(const char *directory) {
  const char *names[] = {"Master.strings.bank", "Master.bank", "music.bank",
                         "sfx.bank"};
  for (int i = 0; i < 4; i++) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", directory, names[i]);
    FMOD_STUDIO_BANK *bank;
    TRY(p_FMOD_Studio_System_LoadBankFile(studio, path,
                                          FMOD_STUDIO_LOAD_BANK_NORMAL, &bank));
    c64_audio_log("C64_AUDIO bank %s", names[i]);
  }
  return 0;
}
int C64AudioUnload(void) {
  if (!studio)
    return 0;
  TRY(p_FMOD_Studio_System_UnloadAll(studio));
  TRY(p_FMOD_Studio_System_FlushCommands(studio));
  mutexLock(&marker_lock);
  marker_read = marker_write = 0;
  mutexUnlock(&marker_lock);
  return 0;
}
int C64AudioShutdown(void) {
  if (!studio)
    return 0;
  int r = p_FMOD_Studio_System_Release(studio);
  studio = NULL;
  c64_audio_log(
      "C64_AUDIO shutdown result=%d mixed=%llu plays=%llu markers=%llu", r,
      (unsigned long long)mix_count, (unsigned long long)play_count,
      (unsigned long long)marker_count);
  return r;
}
int C64AudioPlay(const char *path, const FMOD_3D_ATTRIBUTES *attributes,
                 float volume, uintptr_t *handle) {
  *handle = 0;
  FMOD_STUDIO_EVENTDESCRIPTION *description;
  TRY(p_FMOD_Studio_System_GetEvent(studio, path, &description));
  FMOD_STUDIO_EVENTINSTANCE *event;
  TRY(p_FMOD_Studio_EventDescription_CreateInstance(description, &event));
  int r = 0;
  if (attributes)
    r = p_FMOD_Studio_EventInstance_Set3DAttributes(event, attributes);
  if (!r)
    r = p_FMOD_Studio_EventInstance_SetVolume(event, volume);
  if (!r)
    r = p_FMOD_Studio_EventInstance_Start(event);
  p_FMOD_Studio_EventInstance_Release(event);
  if (!r) {
    *handle = (uintptr_t)event;
    play_count++;
    if (play_count < 30)
      c64_audio_log("C64_AUDIO play %s", path);
  }
  return r;
}
int C64AudioState(FMOD_STUDIO_EVENTINSTANCE *e) {
  FMOD_STUDIO_PLAYBACK_STATE state;
  if (!e || p_FMOD_Studio_EventInstance_GetPlaybackState(e, &state))
    return -1;
  return state;
}
int C64AudioStop(FMOD_STUDIO_EVENTINSTANCE *e) {
  return C64AudioState(e) < 0 ? 0
                              : p_FMOD_Studio_EventInstance_Stop(
                                    e, FMOD_STUDIO_STOP_ALLOWFADEOUT);
}
int C64AudioWatch(FMOD_STUDIO_EVENTINSTANCE *e) {
  return p_FMOD_Studio_EventInstance_SetCallback(
      e, on_marker, FMOD_STUDIO_EVENT_CALLBACK_TIMELINE_MARKER);
}
int C64AudioParameter(FMOD_STUDIO_EVENTINSTANCE *e, const char *n, float v) {
  return C64AudioState(e) < 0
             ? 0
             : p_FMOD_Studio_EventInstance_SetParameterByName(e, n, v, 0);
}
int C64AudioPosition(FMOD_STUDIO_EVENTINSTANCE *e, FMOD_3D_ATTRIBUTES *a,
                     int set) {
  if (C64AudioState(e) < 0)
    return 0;
  return set ? p_FMOD_Studio_EventInstance_Set3DAttributes(e, a)
             : p_FMOD_Studio_EventInstance_Get3DAttributes(e, a);
}
int C64AudioVolume(FMOD_STUDIO_EVENTINSTANCE *e, float *v, int set) {
  if (C64AudioState(e) < 0)
    return 0;
  return set ? p_FMOD_Studio_EventInstance_SetVolume(e, *v)
             : p_FMOD_Studio_EventInstance_GetVolume(e, v, NULL);
}
int C64AudioListener(const FMOD_3D_ATTRIBUTES *a) {
  return p_FMOD_Studio_System_SetListenerAttributes(studio, 0, a, NULL);
}
int C64AudioVCA(const char *n, float v) {
  FMOD_STUDIO_VCA *it;
  TRY(p_FMOD_Studio_System_GetVCA(studio, n, &it));
  return p_FMOD_Studio_VCA_SetVolume(it, v);
}
int C64AudioBus(const char *n, int pause, int immediate) {
  FMOD_STUDIO_BUS *it;
  TRY(p_FMOD_Studio_System_GetBus(studio, n, &it));
  return pause < 0 ? p_FMOD_Studio_Bus_StopAllEvents(
                         it, immediate ? FMOD_STUDIO_STOP_IMMEDIATE
                                       : FMOD_STUDIO_STOP_ALLOWFADEOUT)
                   : p_FMOD_Studio_Bus_SetPaused(it, pause);
}
