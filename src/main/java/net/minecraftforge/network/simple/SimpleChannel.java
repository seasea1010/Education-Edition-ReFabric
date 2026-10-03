package net.minecraftforge.network.simple;
import java.util.function.*;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.network.NetworkEvent;
public class SimpleChannel {
    public <T> void registerMessage(int id, Class<T> type, BiConsumer<T,FriendlyByteBuf> encoder, Function<FriendlyByteBuf,T> decoder, BiConsumer<T,Supplier<NetworkEvent.Context>> handler) {}
}