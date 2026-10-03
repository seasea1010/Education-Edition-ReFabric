package net.minecraftforge.fml.event.lifecycle;
public class FMLCommonSetupEvent { public void enqueueWork(Runnable r){r.run();} }