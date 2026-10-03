package net.minecraftforge.event;
public class TickEvent {
    public enum Phase { START, END }
    public static class ServerTickEvent { public final Phase phase; public ServerTickEvent(){this(Phase.END);} public ServerTickEvent(Phase phase){this.phase=phase;} }
}