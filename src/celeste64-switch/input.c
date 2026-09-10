#include <switch.h>

// SDL's Switch backend defaults to eight players and permits single Joy-Cons.
// Apply the game's policy at initialization, including Mono's input setup.
void __real_padConfigureInput(u32 max_players, u32 style_set);
void __wrap_padConfigureInput(u32 max_players, u32 style_set)
{
    (void)max_players;
    (void)style_set;
    __real_padConfigureInput(1, HidNpadStyleSet_NpadFullCtrl);
}

Result __wrap_hidLaShowControllerSupportForSystem(
    HidLaControllerSupportResultInfo *result_info,
    const HidLaControllerSupportArg *arg, bool flag)
{
    (void)flag;
    HidLaControllerSupportArg single_player = *arg;
    single_player.hdr.player_count_min = 1;
    single_player.hdr.player_count_max = 1;
    single_player.hdr.enable_single_mode = 1;
    single_player.hdr.enable_permit_joy_dual = 1;
    // SDL calls the system variant, whose pairing UI permits unsupported styles.
    // The application variant uses this game's supported styles in the dialog.
    // Single mode means one player and keeps handheld controls available.
    Result rc = hidSetSupportedNpadStyleSet(HidNpadStyleSet_NpadFullCtrl);
    if (R_SUCCEEDED(rc)) rc = hidSetNpadJoyHoldType(HidNpadJoyHoldType_Vertical);
    if (R_FAILED(rc)) return rc;
    return hidLaShowControllerSupport(result_info, &single_player);
}
