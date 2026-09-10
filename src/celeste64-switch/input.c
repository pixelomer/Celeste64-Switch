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

Result __real_hidLaShowControllerSupportForSystem(
    HidLaControllerSupportResultInfo *result_info,
    const HidLaControllerSupportArg *arg, bool flag);

Result __wrap_hidLaShowControllerSupportForSystem(
    HidLaControllerSupportResultInfo *result_info,
    const HidLaControllerSupportArg *arg, bool flag)
{
    HidLaControllerSupportArg single_player = *arg;
    single_player.hdr.player_count_min = 1;
    single_player.hdr.player_count_max = 1;
    single_player.hdr.enable_single_mode = 1;
    single_player.hdr.enable_permit_joy_dual = 1;
    // The supported style set excludes individual Joy-Cons. Single mode here
    // means one player, and preserves handheld use in the connection applet.
    return __real_hidLaShowControllerSupportForSystem(result_info, &single_player, flag);
}
