package net.minecraftforge.registries;
import net.minecraft.core.registries.BuiltInRegistries;
public final class ForgeRegistries {
    public static final IForgeRegistry<net.minecraft.world.item.Item> ITEMS = new IForgeRegistry<>(BuiltInRegistries.ITEM);
    public static final IForgeRegistry<net.minecraft.world.level.block.Block> BLOCKS = new IForgeRegistry<>(BuiltInRegistries.BLOCK);
    public static final IForgeRegistry<net.minecraft.world.level.block.entity.BlockEntityType<?>> BLOCK_ENTITY_TYPES = new IForgeRegistry<>(BuiltInRegistries.BLOCK_ENTITY_TYPE);
    public static final IForgeRegistry<net.minecraft.world.inventory.MenuType<?>> MENU_TYPES = new IForgeRegistry<>(BuiltInRegistries.MENU);
    public static final IForgeRegistry<net.minecraft.sounds.SoundEvent> SOUND_EVENTS = new IForgeRegistry<>(BuiltInRegistries.SOUND_EVENT);
    private ForgeRegistries() {}
}