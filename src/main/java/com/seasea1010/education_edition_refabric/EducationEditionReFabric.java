package com.seasea1010.education_edition_refabric;

import net.mcreator.educationeditionreforged.EducationEditionReforgedMod;
import net.mcreator.educationeditionreforged.network.CompoundCreatorGUIButtonMessage;
import net.mcreator.educationeditionreforged.network.CompoundsPage1ButtonMessage;
import net.mcreator.educationeditionreforged.network.CompoundsPage2ButtonMessage;
import net.mcreator.educationeditionreforged.compat.ForgeCompat.FMLCommonSetupEvent;
import net.fabricmc.api.ModInitializer;

public final class EducationEditionReFabric implements ModInitializer {
    public static final String MOD_ID = "education_edition_reforged";

    @Override
    public void onInitialize() {
        new EducationEditionReforgedMod();

        // Forge's MOD-bus setup event is replaced by explicit registration on Fabric.
        FMLCommonSetupEvent setup = new FMLCommonSetupEvent();
        CompoundCreatorGUIButtonMessage.registerMessage(setup);
        CompoundsPage1ButtonMessage.registerMessage(setup);
        CompoundsPage2ButtonMessage.registerMessage(setup);

        System.out.println("[Education Edition ReFabric] Initialized.");
    }
}
