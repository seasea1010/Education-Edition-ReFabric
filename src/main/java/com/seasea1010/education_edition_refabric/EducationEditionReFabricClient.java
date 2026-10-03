package com.seasea1010.education_edition_refabric;

import net.fabricmc.api.ClientModInitializer;
import net.mcreator.educationeditionreforged.compat.ForgeCompat.FMLClientSetupEvent;
import net.mcreator.educationeditionreforged.init.EducationEditionReforgedModScreens;

public final class EducationEditionReFabricClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        EducationEditionReforgedModScreens.clientLoad(new FMLClientSetupEvent());
    }
}
