package net.minecraftforge.registries;
import java.util.function.Supplier;
public class RegistryObject<T> implements Supplier<T> {
    private final T value;
    private final String id;
    public RegistryObject(String id, T value) { this.id=id; this.value=value; }
    public T get() { return value; }
    public String getId() { return id; }
}