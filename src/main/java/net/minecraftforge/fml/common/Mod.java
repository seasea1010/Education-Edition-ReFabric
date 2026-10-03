package net.minecraftforge.fml.common;
import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE)
public @interface Mod {
    String value() default "";
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE)
    @interface EventBusSubscriber {
        Bus bus() default Bus.GAME;
        net.minecraftforge.api.distmarker.Dist[] value() default {};
        enum Bus { GAME, MOD }
    }
}