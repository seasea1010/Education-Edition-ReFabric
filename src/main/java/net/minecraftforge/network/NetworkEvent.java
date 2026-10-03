package net.minecraftforge.network;
import net.minecraft.server.level.ServerPlayer;
public final class NetworkEvent {
    public static class Context {
        private ServerPlayer sender;
        private boolean handled;
        public Context() {}
        public Context(ServerPlayer sender){this.sender=sender;}
        public void enqueueWork(Runnable r){r.run();}
        public ServerPlayer getSender(){return sender;}
        public void setPacketHandled(boolean handled){this.handled=handled;}
    }
}