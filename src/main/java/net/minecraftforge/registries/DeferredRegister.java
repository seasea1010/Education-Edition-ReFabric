package net.minecraftforge.registries;
import java.util.function.Supplier;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.core.Registry;
import net.minecraftforge.eventbus.api.IEventBus;
public class DeferredRegister<T> {
    private final IForgeRegistry<T> registry;
    private final String modid;
    private DeferredRegister(IForgeRegistry<T> registry, String modid) { this.registry=registry; this.modid=modid; }
    public static <T> DeferredRegister<T> create(IForgeRegistry<T> registry, String modid) { return new DeferredRegister<>(registry, modid); }
    public RegistryObject<T> register(String name, Supplier<? extends T> supplier) {
        T value=supplier.get();
        T registered=Registry.register(registry.vanilla(), new ResourceLocation(modid, name), value);
        return new RegistryObject<>(name, registered);
    }
    public void register(IEventBus bus) {}
}