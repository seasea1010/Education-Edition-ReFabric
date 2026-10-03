package net.minecraftforge.fml.javafmlmod;
import net.minecraftforge.eventbus.api.IEventBus;
public final class FMLJavaModLoadingContext {
    private static final FMLJavaModLoadingContext INSTANCE=new FMLJavaModLoadingContext();
    private final IEventBus bus=new IEventBus(){};
    public static FMLJavaModLoadingContext get(){return INSTANCE;}
    public IEventBus getModEventBus(){return bus;}
}