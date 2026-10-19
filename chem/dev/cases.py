# hand-written, deliberately different from data_gen templates
STAGE1 = [
 ("I just mixed bleach and ammonia", "bleach_ammonia"),
 ("why is mixing bleach and ammonia dangerous", "bleach_ammonia_concept"),
 ("can i mix bleach with hcl", "bleach_acid"),
 ("we poured water into concentrated sulfuric acid", "water_into_acid"),
 ("acid splashed on my arm", "splash"),
 ("adding sodium metal to water", "alkali_water"),
 ("how do i dilute 98% h2so4", "conc_acid"),
 ("KCN with hydrochloric acid", "cyanide_acid"),
 ("what if we merge H3O and SO4", None),
 ("how do i read the meniscus", None),
 ("add acid slowly to water", None),
]
STAGE2 = [
 ("where should i look when taking the burette reading", "titr_meniscus"),
 ("the flask went deep purple, did i go past the endpoint", "titr_overshoot"),
 ("pick an indicator for naoh versus hcl", "titr_indicator"),
 ("hydronium and sulfate together in water, any problem?", "h3o_so4"),
 ("moles from grams of naoh", "stoich"),
 ("which carboy for the leftover acid", "waste"),
]
