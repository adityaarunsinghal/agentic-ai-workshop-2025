## The Jajaja Protocol: Ingrid's Dining Journey

It's Saturday afternoon at Jajaja, the bustling vegan Mexican restaurant near the World Trade Center. Ingrid enters, excited to finally try this place her coworker won't stop raving about. Pedro, the **Restaurant Manager**, greets her warmly and seats her by the window overlooking Greenwich Street. Behind the scenes, Pedro coordinates the entire dining experience, managing all the moving parts that make a great meal happen.

The restaurant operates with two main **Kitchen Stations**:
1. **Main Kitchen Station** - the in-house kitchen where Head Chef Miguel works (**face-to-face communication**)
2. **Dessert Partner** - "Dulce Vegan Bakery" three blocks away (**phone/tablet ordering**)

Pedro assigns two **Waiters** to handle Ingrid's table: Maria for the main kitchen (walking orders directly to Chef Miguel) and Carlos for external orders (using the restaurant's tablet system for Dulce Bakery).

After settling in with water and chips, Ingrid opens the menu. At the top, she notices colorful **Pre-Set Meal Combos**: "Taco Tuesday Fiesta", "Weekend Brunch Special", and "Quick Lunch Express". Pedro explains to Ingrid that each kitchen has displayed their specially curated combinations here. Intrigued by the idea of brunch at 2 PM, Ingrid selects "Weekend Brunch Special" and tells Maria she'd like medium spice, yes to drink pairings, and regular portions.

This **pre-set combo** gives Chef Miguel - the only one besides Ingrid with true **reasoning ability** in this entire restaurant - structured guidance for crafting her meal. Miguel isn't just following recipes; he's the "brains" who makes creative decisions, adapts to what's freshest today, and orchestrates the entire kitchen flow. Everyone else in the system - waiters, prep cooks, even Pedro - are simply following protocols and relaying information. Chef Miguel is the highest paid employee in the restaurant, and he is also the most recent hire. He has a lot of experience from the outside world but in JaJaJa its still early days, so he is learning. He also has to read up on what the kitchen had called the "Weekend Brunch Special" etc.

Chef Miguel starts planning. *"Weekend brunch with medium spice... let me build something special with what came in fresh this morning,"* he thinks. He mentally reviews what the kitchens had told him about their appliances etc. or **cooking operations** which the kitchen can perform today: grill vegetables, prepare fresh salsas, assemble tacos, make guacamole, press tortillas.

He decides on loaded nachos as the centerpiece. He tells Maria: "Start with salsa verde, medium heat, extra lime." Maria takes this straight to the prep station through **direct communication**, with a little notepad.

Five minutes later, Maria returns to Ingrid's table with an **order status update**: "Kitchen wanted me to let you know everything is being made fresh to order - your meal should be ready in about 15 minutes." Ingrid appreciates the update - *so much better than wondering if they forgot about her*.

The Main Kitchen maintains several **menu items and ingredients** as reference materials - laminated recipe cards and binders that anyone can review:
- loaded nachos with salsa verde Recipe Card
- Black Bean Preparation Guide
- Weekend Specials Ingredient List
- Complete Allergen & Nutrition Information Binder

Ingrid has been trying to increase her protein intake, so she asks Maria: "Could I see the nutrition information?" Maria brings over the nutrition binder (**resource**) for Ingrid to review. Simultaneously in the kitchen, Chef Miguel is consulting an identical binder to check which items are highest in protein for her meal. This isn't a **cooking operation** - it's simply accessing information. The **Kitchen Station** makes these **recipe and ingredient resources** available to anyone who needs them, no cooking required, just open information.

As the Main Kitchen begins assembling the loaded nachos, the station needs clarification. Maria approaches with a **preference check**: "The kitchen needs to know - would you like your tortilla chips extra crispy, or the default crispiness for your loaded nachos?"

Ingrid sees **three clear response options** in this moment:
- **Accept**: Say yes to extra crispy
- **Decline**: Say no, preferring normal
- **Dismiss**: Can't decide right now

*"Definitely crispy,"* she thinks. "Extra crispy please!" she tells Maria, who relays this **acceptance** back to the kitchen. Had she preferred normal, that would be a **decline** of the crispy option. If she'd been unsure, she could have **dismissed** the question to decide later or let the kitchen take the call.
The kitchen prefers to be careful about these kinds of things, so even if Chef Miguel had not thought to ask this crispiness question, Maria would have still been sent by the kitchen straight to Ingrid to ask about this.

While the main course is being prepared, Chef Miguel realizes he needs dessert options. He signals Carlos to check availability. Carlos uses the **tablet ordering** system to query Dulce Bakery's current selection.

Suddenly, Maria returns with an **alert**: "The bar has been experimenting with a new Spicy Mango Margarita - Chef Miguel thinks it would pair perfectly with your loaded nachos today!" This demonstrates **station independence** - the bar developed this new item on their own, without knowing what specific meals are being prepared.

Midway through preparation, the prep cook encounters an unexpected challenge with the mole-inspired drizzle. They need Chef Miguel's expertise, requesting a **head chef consultation**: "Chef, how do I balance these flavors?"

*Miguel tastes it, his experienced palate immediately identifying the issue.* "Add a touch of apple cider vinegar and a pinch more cacao," he instructs. This **consultation** shows the kitchen station requesting help from Miguel - the only one with the reasoning ability to solve creative problems.

Ten minutes later, Maria returns: "Your loaded nachos are just being plated now!"

Pedro, the **Restaurant Manager**, keeps everything running smoothly throughout. He ensures Maria and Carlos (**waiters**) stay in their lanes and always have the right notes with them, and maintains **station independence**. The Main Kitchen never learns Dulce Bakery's secret rasberry chocolate recipe, and the bakery has no idea what main courses Jajaja is serving today.

Finally, everything comes together. The loaded nachos arrive perfectly crispy with hemp crema drizzled on top, the Spicy Mango Margarita provides a perfect complement, and later, the rasberry chocolate cheesecake from Dulce Bakery arrives fresh. The Main Kitchen never touched that dessert, maintaining complete **station independence** throughout service.

*Ingrid takes her first bite of the perfectly crispy loaded nachos and thinks: "My coworker was absolutely right about this place."* Her Saturday afternoon brunch was orchestrated by Pedro the **Restaurant Manager** and his **waiters**, coordinating two independent kitchen stations through different **communication methods**, with Chef Miguel's intelligent decisions guiding every step of the culinary experience.

---

## MCP to Restaurant Mapping

| MCP Concept | Restaurant Analogy |
|------------|-------------------|
| **MCP Host** | **Restaurant Manager** (Pedro) |
| **MCP Clients** | **Waiters** (Maria, Carlos) |
| **MCP Servers** | **Kitchen Stations** (Main Kitchen, Dessert Partner) |
| **Tools** | **Cooking Operations** (grill vegetables, prepare salsa, etc.) |
| **Resources** | **Menu Items and Ingredients** (recipes, nutrition info, allergen lists) |
| **Prompts** | **Pre-Set Meal Combos** (Weekend Brunch Special, etc.) |
| **Elicitation** | **Preference Check** (crispy vs. soft tortillas) |
| **Sampling** | **Head Chef Consultation** (asking chef for creative solutions) |
| **Notifications** | **Alerts** (new margarita available) |
| **Progress Tracking** | **Order Status Updates** (your meal will be ready in 15 minutes) |
| **Server Isolation** | **Station Independence** (kitchen doesn't see bakery's recipes) |
| **stdio Transport** | **Face-to-Face Communication** (waiter walks to kitchen) |
| **HTTP Transport** | **Phone/Tablet Ordering** (digital orders to external bakery) |
| **Three-Action Model** | **Three-Response Preference Model** (accept/decline/dismiss) |

Additional mappings:
- **LLM** = **Head Chef Miguel** (the reasoning brain of the operation)
- **User** = **Restaurant Customer** (Ingrid)
- **JSON-RPC Messages** = **Order Tickets and Requests**
