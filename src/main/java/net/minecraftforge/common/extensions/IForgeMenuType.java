package net.minecraftforge.common.extensions;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.flag.FeatureFlags;
public final class IForgeMenuType {
    public interface Factory<T> { T create(int id, Inventory inv, FriendlyByteBuf buf); }
    public static <T extends net.minecraft.world.inventory.AbstractContainerMenu> MenuType<T> create(Factory<T> factory) {
        return new MenuType<>((id, inv, buf) -> factory.create(id, inv, buf), FeatureFlags.VANILLA_SET);
    }
}