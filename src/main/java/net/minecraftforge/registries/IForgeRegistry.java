package net.minecraftforge.registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.core.Registry;
public class IForgeRegistry<T> {
    final Registry<T> registry;
    public IForgeRegistry(Registry<T> registry) { this.registry=registry; }
    public T getValue(ResourceLocation id) { return registry.get(id); }
    public ResourceLocation getKey(T value) { return registry.getKey(value); }
    public Registry<T> vanilla() { return registry; }
}