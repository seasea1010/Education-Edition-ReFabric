package net.minecraftforge.network;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.MenuProvider;
public final class NetworkHooks {
    public static void openScreen(ServerPlayer player, MenuProvider provider){ player.openMenu(provider); }
}