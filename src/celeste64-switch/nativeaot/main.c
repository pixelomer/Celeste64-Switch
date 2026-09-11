// NativeAOT remains loaded until the application process exits.
#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/iosupport.h>
#include <errno.h>
#include <unicode/udata.h>
#include <unicode/ulocdata.h>

u32 __nx_applet_exit_mode = 1;
extern void C64ManagedMain(void);
static FILE* managedLog;
static FILE* runtimeLog;
static ssize_t write_log(struct _reent* reent, const char* bytes, size_t size, FILE* file)
{
    size_t written = fwrite(bytes,1,size,file);
    if (fflush(file) || (written == 0 && size)) { reent->_errno=errno; return -1; }
    return (ssize_t)written;
}
static ssize_t managed_write(struct _reent* r, void* fd, const char* bytes, size_t size)
{ (void)fd; return write_log(r,bytes,size,managedLog); }
static ssize_t runtime_write(struct _reent* r, void* fd, const char* bytes, size_t size)
{ (void)fd; return write_log(r,bytes,size,runtimeLog); }
static const devoptab_t managedOutput = {.name="c64stdout",.write_r=managed_write};
static const devoptab_t runtimeOutput = {.name="c64stderr",.write_r=runtime_write};

static int initialize_icu(void)
{
    FILE* file = fopen("romfs:/icudt77l.dat", "rb");
    if (!file) return 0;
    if (fseek(file, 0, SEEK_END)) { fclose(file); return 0; }
    long length = ftell(file);
    if (length <= 0 || fseek(file, 0, SEEK_SET)) { fclose(file); return 0; }
    void* data = malloc((size_t)length);
    if (!data) { fclose(file); return 0; }
    size_t count = fread(data, 1, (size_t)length, file);
    fclose(file);
    if (count != (size_t)length) { free(data); return 0; }
    UErrorCode status = U_ZERO_ERROR;
    udata_setCommonData(data, &status);
    UVersionInfo version;
    if (U_SUCCESS(status)) ulocdata_getCLDRVersion(version, &status);
    if (U_FAILURE(status)) {
        fprintf(stderr, "ICU initialization: %s\n", u_errorName(status));
        // ICU may retain data even after an initialization error. Process exit
        // owns cleanup; never free storage still visible to runtime workers.
        return 0;
    }
    fprintf(stderr, "ICU CLDR %u.%u.%u.%u\n", version[0],version[1],version[2],version[3]);
    return 1;
}
int main(int argc, char** argv)
{
    (void)argc; (void)argv;
    mkdir("sdmc:/switch",0777);
    mkdir("sdmc:/switch/celeste64",0777);
    mkdir("sdmc:/switch/celeste64/userdata",0777);
    managedLog=fopen("sdmc:/switch/celeste64/nativeaot.log", "w");
    runtimeLog=fopen("sdmc:/switch/celeste64/nativeaot-runtime.log", "w");
    if (!managedLog || !runtimeLog) return 1;
    // Preserve descriptors 1/2 used by System.Console. newlib freopen can
    // allocate another descriptor, which does not redirect managed Console.
    devoptab_list[STD_OUT]=&managedOutput;
    devoptab_list[STD_ERR]=&runtimeOutput;
    setvbuf(stdout,NULL,_IONBF,0);
    setvbuf(stderr,NULL,_IONBF,0);
    fprintf(stderr,"BEGIN Celeste64 1.2.0 NativeAOT / full FMOD 2.02.18\n");
    Result rc = romfsInit();
    if (R_FAILED(rc)) { fprintf(stderr,"romfsInit %x\n",rc); return 1; }
    if (!initialize_icu()) return 1;
    C64ManagedMain();
    fprintf(stderr,"END managed entry returned\n");
    // Keep ICU, GC, TLS and mappings alive until libnx requests process exit.
    return 0;
}
