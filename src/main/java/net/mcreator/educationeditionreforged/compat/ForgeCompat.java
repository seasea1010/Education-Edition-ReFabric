package net.mcreator.educationeditionreforged.compat;

import java.util.*;
import java.util.function.*;
import net.minecraft.core.*;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.*;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.*;
import net.minecraft.world.inventory.*;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.entity.*;
import net.minecraft.world.level.block.state.*;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.Container;
import net.minecraft.world.WorldlyContainer;

public final class ForgeCompat {
    private ForgeCompat() {}

    public interface IEventBus { default void register(Object o) {} }
    public static final IEventBus EVENT_BUS = new IEventBus(){};

    public enum Dist { CLIENT, DEDICATED_SERVER }
    public enum Phase { START, END }
    public static final class TickEvent { public enum Phase { START, END } public static class ServerTickEvent { public final Phase phase; public ServerTickEvent(){this.phase=Phase.END;} public ServerTickEvent(Phase p){phase=p;} } public static class PlayerTickEvent { public final Phase phase; public final Player player; public PlayerTickEvent(Player p, Phase ph){player=p;phase=ph;} } }

    public static class FMLCommonSetupEvent { public void enqueueWork(Runnable r){r.run();} }
    public static class FMLClientSetupEvent { public void enqueueWork(Runnable r){r.run();} }
    public static final class FMLJavaModLoadingContext {
        private static final FMLJavaModLoadingContext I=new FMLJavaModLoadingContext();
        public static FMLJavaModLoadingContext get(){return I;}
        public IEventBus getModEventBus(){return EVENT_BUS;}
    }
    public static final class SidedThreadGroups { public static final ThreadGroup SERVER=new ThreadGroup("SERVER"); }

    public static final class ModList {
        private static final ModList I=new ModList();
        public static ModList get(){return I;}
        public boolean isLoaded(String id){return false;}
    }

    public static final class MinecraftForge { public static final IEventBus EVENT_BUS=ForgeCompat.EVENT_BUS; }

    public static class Capability<T> {}
    public static final class ForgeCapabilities { public static final Capability<IItemHandler> ITEM_HANDLER=new Capability<>(); }

    public static class LazyOptional<T> {
        private final T value; private boolean valid=true;
        private LazyOptional(T value){this.value=value;}
        public static <T> LazyOptional<T> of(Supplier<T> s){return new LazyOptional<>(s.get());}
        public static <T> LazyOptional<T> empty(){return new LazyOptional<>(null);}
        public void ifPresent(Consumer<? super T> c){if(valid&&value!=null)c.accept(value);}
        @SuppressWarnings("unchecked") public <R> LazyOptional<R> cast(){return (LazyOptional<R>)this;}
        public void invalidate(){valid=false;}
    }

    public interface IItemHandler {
        int getSlots(); ItemStack getStackInSlot(int slot);
        ItemStack insertItem(int slot, ItemStack stack, boolean simulate);
        ItemStack extractItem(int slot,int amount,boolean simulate);
        int getSlotLimit(int slot); boolean isItemValid(int slot,ItemStack stack);
    }
    public interface IItemHandlerModifiable extends IItemHandler { void setStackInSlot(int slot,ItemStack stack); }

    public static class ItemStackHandler implements IItemHandlerModifiable {
        protected final ItemStack[] stacks;
        public ItemStackHandler(int size){stacks=new ItemStack[size];Arrays.fill(stacks,ItemStack.EMPTY);}
        public int getSlots(){return stacks.length;}
        public ItemStack getStackInSlot(int s){return s>=0&&s<stacks.length?stacks[s]:ItemStack.EMPTY;}
        public void setStackInSlot(int s,ItemStack st){if(s>=0&&s<stacks.length)stacks[s]=st==null?ItemStack.EMPTY:st;}
        public ItemStack insertItem(int s,ItemStack st,boolean sim){
            if(st==null||st.isEmpty())return ItemStack.EMPTY; ItemStack cur=getStackInSlot(s); int max=getSlotLimit(s);
            if(!cur.isEmpty()&&!ItemStack.isSameItemSameTags(cur,st))return st;
            if(cur.isEmpty()){int n=Math.min(max,st.getCount());if(!sim){ItemStack c=st.copy();c.setCount(n);setStackInSlot(s,c);}if(n==st.getCount())return ItemStack.EMPTY;ItemStack r=st.copy();r.shrink(n);return r;}
            int room=max-cur.getCount();if(room<=0)return st;int n=Math.min(room,st.getCount());if(!sim)cur.grow(n);if(n==st.getCount())return ItemStack.EMPTY;ItemStack r=st.copy();r.shrink(n);return r;
        }
        public ItemStack extractItem(int s,int amount,boolean sim){ItemStack cur=getStackInSlot(s);if(cur.isEmpty()||amount<=0)return ItemStack.EMPTY;int n=Math.min(amount,cur.getCount());ItemStack out=cur.copy();out.setCount(n);if(!sim){cur.shrink(n);setStackInSlot(s,cur);}return out;}
        public int getSlotLimit(int s){return 64;} public boolean isItemValid(int s,ItemStack st){return true;}
    }

    private static class ContainerHandler implements IItemHandler {
        final Container c; ContainerHandler(Container c){this.c=c;}
        public int getSlots(){return c.getContainerSize();} public ItemStack getStackInSlot(int s){return c.getItem(s);}
        public ItemStack insertItem(int s,ItemStack st,boolean sim){if(!c.canPlaceItem(s,st))return st;if(sim)return st.copy();c.setItem(s,st);c.setChanged();return ItemStack.EMPTY;}
        public ItemStack extractItem(int s,int n,boolean sim){ItemStack cur=c.getItem(s);if(cur.isEmpty())return ItemStack.EMPTY;ItemStack out=cur.copy();out.setCount(Math.min(n,cur.getCount()));if(!sim)c.removeItem(s,out.getCount());return out;}
        public int getSlotLimit(int s){return 64;} public boolean isItemValid(int s,ItemStack st){return c.canPlaceItem(s,st);}
    }

    public static LazyOptional<IItemHandler> getItemHandler(Object obj){
        if(obj instanceof BlockEntity be && be instanceof Container c)return LazyOptional.of(()->new ContainerHandler(c));
        if(obj instanceof Entity e && e instanceof Player p)return LazyOptional.of(()->new ContainerHandler(p.getInventory()));
        return LazyOptional.empty();
    }

    public static class SlotItemHandler extends Slot {
        private final IItemHandler h; private final int hs;
        public SlotItemHandler(IItemHandler h,int slot,int x,int y){super(new Adapter(h),slot,x,y);this.h=h;this.hs=slot;}
        public ItemStack getItem(){return h.getStackInSlot(hs);}
        public boolean hasItem(){return !getItem().isEmpty();}
        public void set(ItemStack st){if(h instanceof IItemHandlerModifiable m)m.setStackInSlot(hs,st);else h.insertItem(hs,st,false);}
        public ItemStack remove(int n){return h.extractItem(hs,n,false);}
        public boolean mayPlace(ItemStack st){return h.isItemValid(hs,st);}
        public int getMaxStackSize(){return h.getSlotLimit(hs);}
        private static class Adapter implements Container {
            final IItemHandler h; Adapter(IItemHandler h){this.h=h;}
            public int getContainerSize(){return h.getSlots();} public boolean isEmpty(){for(int i=0;i<h.getSlots();i++)if(!h.getStackInSlot(i).isEmpty())return false;return true;}
            public ItemStack getItem(int i){return h.getStackInSlot(i);} public ItemStack removeItem(int i,int n){return h.extractItem(i,n,false);}
            public ItemStack removeItemNoUpdate(int i){return h.extractItem(i,64,false);} public void setItem(int i,ItemStack s){if(h instanceof IItemHandlerModifiable m)m.setStackInSlot(i,s);}
            public void setChanged(){} public boolean stillValid(Player p){return true;} public void clearContent(){for(int i=0;i<h.getSlots();i++)if(h instanceof IItemHandlerModifiable m)m.setStackInSlot(i,ItemStack.EMPTY);}
        }
    }

    public static class SidedInvWrapper implements IItemHandler {
        final WorldlyContainer inv; final Direction side;
        public SidedInvWrapper(WorldlyContainer inv,Direction side){this.inv=inv;this.side=side;}
        public static LazyOptional<? extends IItemHandler>[] create(WorldlyContainer inv,Direction[] dirs){LazyOptional<? extends IItemHandler>[] a=new LazyOptional[dirs.length];for(int i=0;i<dirs.length;i++){Direction d=dirs[i];a[i]=LazyOptional.of(()->new SidedInvWrapper(inv,d));}return a;}
        public int getSlots(){return inv.getContainerSize();} public ItemStack getStackInSlot(int s){return inv.getItem(s);}
        public ItemStack insertItem(int s,ItemStack st,boolean sim){if(!inv.canPlaceItemThroughFace(s,st,side))return st;if(sim)return st.copy();inv.setItem(s,st);return ItemStack.EMPTY;}
        public ItemStack extractItem(int s,int n,boolean sim){ItemStack cur=inv.getItem(s);if(cur.isEmpty()||!inv.canTakeItemThroughFace(s,cur,side))return ItemStack.EMPTY;return sim?cur.copy():inv.removeItem(s,n);}
        public int getSlotLimit(int s){return 64;} public boolean isItemValid(int s,ItemStack st){return inv.canPlaceItemThroughFace(s,st,side);}
    }

    public static class RegistryObject<T> implements Supplier<T> {
        final T value; final ResourceLocation id; RegistryObject(ResourceLocation id,T value){this.id=id;this.value=value;}
        public T get(){return value;} public ResourceLocation getId(){return id;}
    }
    public static class IForgeRegistry<T> {
        final Registry<T> registry; IForgeRegistry(Registry<T> r){registry=r;}
        public T getValue(ResourceLocation id){return registry.get(id);} @SuppressWarnings("unchecked") public ResourceLocation getKey(Object value){return registry.getKey((T)value);}
    }
    public static final class ForgeRegistries {
        public static final IForgeRegistry<Item> ITEMS=new IForgeRegistry<>(BuiltInRegistries.ITEM);
        public static final IForgeRegistry<Block> BLOCKS=new IForgeRegistry<>(BuiltInRegistries.BLOCK);
        public static final IForgeRegistry<BlockEntityType<?>> BLOCK_ENTITY_TYPES=new IForgeRegistry<>(BuiltInRegistries.BLOCK_ENTITY_TYPE);
        public static final IForgeRegistry<MenuType<?>> MENU_TYPES=new IForgeRegistry<>(BuiltInRegistries.MENU);
        public static final IForgeRegistry<SoundEvent> SOUND_EVENTS=new IForgeRegistry<>(BuiltInRegistries.SOUND_EVENT);
    }
    public static class DeferredRegister<T> {
        final IForgeRegistry<T> registry; final String modid;
        DeferredRegister(IForgeRegistry<T> r,String id){registry=r;modid=id;}
        public static <T> DeferredRegister<T> create(IForgeRegistry<T> r,String id){return new DeferredRegister<>(r,id);} @SuppressWarnings({"unchecked","rawtypes"}) public static <T> DeferredRegister<T> create(net.minecraft.resources.ResourceKey key,String id){ if(key==net.minecraft.core.registries.Registries.CREATIVE_MODE_TAB) return new DeferredRegister(new IForgeRegistry(BuiltInRegistries.CREATIVE_MODE_TAB),id); throw new IllegalArgumentException(key.toString()); }
        public <U extends T> RegistryObject<U> register(String name,Supplier<? extends U> sup){U v=Registry.register(registry.registry,new ResourceLocation(modid,name),sup.get());return new RegistryObject<>(new ResourceLocation(modid,name),v);}
        public void register(IEventBus bus){}
    }

    public static final class IForgeMenuType {
        public interface Factory<T>{T create(int id,Inventory inv,FriendlyByteBuf buf);}
        public static <T extends AbstractContainerMenu> MenuType<T> create(Factory<T> f){return new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType<>((id,inv,buf)->f.create(id,inv,buf));}
    }

    public static final class NetworkHooks { public static void openScreen(ServerPlayer p,MenuProvider provider){p.openMenu(provider);} public static void openScreen(ServerPlayer p,MenuProvider provider,BlockPos pos){p.openMenu(provider);} }
    public static final class NetworkRegistry { public static SimpleChannel newSimpleChannel(ResourceLocation id,Supplier<String> p,Predicate<String> c,Predicate<String> s){return new SimpleChannel();} }
    public static class SimpleChannel { public <T> void registerMessage(int id,Class<T> t,BiConsumer<T,FriendlyByteBuf> e,Function<FriendlyByteBuf,T>d,BiConsumer<T,Supplier<NetworkEvent.Context>>h){} }
    public static final class NetworkEvent {
        public static class Context { private final ServerPlayer sender; public Context(){this(null);} public Context(ServerPlayer s){sender=s;} public void enqueueWork(Runnable r){r.run();} public ServerPlayer getSender(){return sender;} public void setPacketHandled(boolean b){} }
    }

    public static final class Mod {}
    
    public static final class BrewingRecipeRegistry { public static void addRecipe(IBrewingRecipe r){} }
    public interface IBrewingRecipe { boolean isInput(ItemStack s); boolean isIngredient(ItemStack s); ItemStack getOutput(ItemStack in,ItemStack ing); }

    public static void tickServer(Runnable r) { }
    public static class ForgeEventSubscriber {}
}