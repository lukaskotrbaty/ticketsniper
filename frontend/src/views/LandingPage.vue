<script setup lang="ts">
import { RouterLink } from 'vue-router';
import {
  MapPinIcon,
  CursorArrowRaysIcon,
  EnvelopeIcon,
  ClockIcon,
  BoltIcon,
  HandThumbUpIcon,
  EyeIcon,
  GiftIcon,
} from '@heroicons/vue/24/outline';

const currentYear = new Date().getFullYear();

</script>

<template>
  <div class="min-h-screen bg-background-body text-text-secondary">
    <main>
      <!-- 1. Hero Section -->
      <section class="bg-gradient-to-r from-gradient-indigo-start to-gradient-indigo-end py-20 text-center">
        <div class="container mx-auto px-4">
          <img src="@/assets/Crosshair.svg" alt="Ticket Sniper logo - zaměřovač na lístky RegioJet" class="h-16 w-16 text-primary-light mx-auto mb-6" />
          <h1 class="text-4xl md:text-5xl font-bold mb-4 text-text-primary">
            Vyprodaný spoj RegioJet? Ticket Sniper vám uloví volné místo. <strong class="text-primary-dark">ZDARMA!</strong>
          </h1>
          <p class="text-lg md:text-xl text-text-secondary mb-8 max-w-3xl mx-auto">
            Už vás nebaví neustále kontrolovat, zda se neuvolnil lístek na váš vytoužený, ale bohužel vyprodaný spoj RegioJet? Ticket Sniper je řešení! Nastavte si hlídání volných míst RegioJet během minuty a my vám zdarma pošleme e‑mailovou notifikaci na volné lístky, jakmile se objeví.
          </p>
          <RouterLink
            to="/register"
            class="px-8 py-3 bg-primary text-text-on-primary rounded-lg hover:bg-primary-dark text-lg font-semibold shadow-md transition duration-300"
          >
            Chci ulovit lístek ZDARMA
          </RouterLink>
        </div>
      </section>

      <!-- 2. How Ticket Sniper works? -->
      <section id="how-it-works" class="py-16 bg-background-card">
        <div class="container mx-auto px-4 text-center">
          <h2 class="text-3xl font-bold mb-12 text-text-primary">Jak ulovit lístek na vyprodaný spoj RegioJet ve <strong class="text-primary-dark">3 snadných krocích</strong></h2>
          <div class="grid md:grid-cols-3 gap-10">
            <!-- Step 1 -->
            <div class="flex flex-col items-center">
              <MapPinIcon class="h-12 w-12 text-primary mb-4" />
              <h3 class="text-xl font-semibold mb-2 text-text-primary">Zadejte cíl cesty</h3>
              <p class="text-text-secondary">
                V naší aplikaci si vyberte trasu (odkud, kam), datum a konkrétní čas odjezdu spoje společnosti Regiojet, na který máte "zálusk", i když je momentálně RegioJet plno.
              </p>
            </div>
            <!-- Step 2 -->
            <div class="flex flex-col items-center">
              <CursorArrowRaysIcon class="h-12 w-12 text-primary mb-4" />
              <h3 class="text-xl font-semibold mb-2 text-text-primary">Spusťte hlídání lístků</h3>
              <p class="text-text-secondary">
                Jedním kliknutím aktivujte Ticket Sniper. Náš systém začne automaticky a pravidelně pátrat po volném místě a provádět sledování dostupnosti RegioJet na vámi vybraném spoji.
              </p>
            </div>
            <!-- Step 3 -->
            <div class="flex flex-col items-center">
              <EnvelopeIcon class="h-12 w-12 text-primary mb-4" />
              <h3 class="text-xl font-semibold mb-2 text-text-primary">Cíl zasažen! Volné místo nalezeno!</h3>
              <p class="text-text-secondary">
                Jakmile Ticket Sniper "uloví" volné místo na dříve obsazeném spoji RegioJet, okamžitě vám pošleme upozornění na volné lístky RegioJet e‑mailem. Vy pak můžete rychle přejít na web dopravce a lístek zakoupit.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- 3. Benefits Section -->
      <section id="benefits" class="py-16 bg-background-alt">
        <div class="container mx-auto px-4">
          <h2 class="text-3xl font-bold text-center mb-12 text-text-primary">S Ticket Sniper máte navrch při shánění lístků na vyprodané spoje RegioJet</h2>
          <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <!-- Benefit 1 -->
            <div class="bg-background-card p-6 rounded-lg shadow-md flex items-start space-x-4">
              <ClockIcon class="h-10 w-10 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 class="text-xl font-semibold mb-2 text-text-primary">Nonstop pátrání za vás</h3>
                <p class="text-text-secondary">
                  Už nemusíte trávit čas neustálým obnovováním stránek dopravce. Ticket Sniper neúnavně kontroluje dostupnost lístků RegioJet za vás, ve dne v noci, a hlídá uvolněná místa.
                </p>
              </div>
            </div>
            <!-- Benefit 2 -->
            <div class="bg-background-card p-6 rounded-lg shadow-md flex items-start space-x-4">
              <BoltIcon class="h-10 w-10 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 class="text-xl font-semibold mb-2 text-text-primary">Buďte první na ráně</h3>
                <p class="text-text-secondary">
                  Jakmile se místo uvolní, Ticket Sniper "vystřelí" e‑mail. Rychlost je klíčová pro úspěšný zásah žádaného lístku, zvláště když jsou RegioJet spoje vyprodané!
                </p>
              </div>
            </div>
            <!-- Benefit 3 -->
            <div class="bg-background-card p-6 rounded-lg shadow-md flex items-start space-x-4">
              <HandThumbUpIcon class="h-10 w-10 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 class="text-xl font-semibold mb-2 text-text-primary">Nastaveno na pár kliknutí</h3>
                <p class="text-text-secondary">
                  Žádné složité nastavování. Zadat spoj a spustit automatické hlídání RegioJet je otázkou okamžiku.
                </p>
              </div>
            </div>
            <!-- Benefit 4 -->
            <div class="bg-background-card p-6 rounded-lg shadow-md flex items-start space-x-4">
              <EyeIcon class="h-10 w-10 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 class="text-xl font-semibold mb-2 text-text-primary">Přesně zaměřeno na spoje Regiojet</h3>
                <p class="text-text-secondary">
                  Specializujeme se na monitorování autobusových a vlakových spojů společnosti Regiojet. Naše "optika" je nastavena na jejich systém a pomůže vám zjistit, kdy se uvolní místo v RegioJetu.
                </p>
              </div>
            </div>
             <!-- Benefit 5 -->
            <div class="bg-background-card p-6 rounded-lg shadow-md flex items-start space-x-4">
              <GiftIcon class="h-10 w-10 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 class="text-xl font-semibold mb-2 text-text-primary">Lovte bez poplatků</h3>
                <p class="text-text-secondary">
                  Začněte hlídání vyprodaných spojů RegioJet bez jakýchkoli nákladů. Registrace a používání Ticket Sniper je kompletně zdarma.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 4. Testimonials Section (Placeholder) -->
      <section id="testimonials" class="py-16 bg-background-card">
        <div class="container mx-auto px-4 text-center">
          <h2 class="text-3xl font-bold mb-12 text-text-primary">Co říkají naši Snipeři o hledání lístků na RegioJet</h2>
          <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div class="bg-background-body p-6 rounded-lg shadow-sm text-left">
              <p class="text-text-secondary italic mb-4">
                "Konečně jsem ulovil lístek na páteční spoj RegioJet domů, který byl týdny vyprodaný! Díky e‑mailu z Ticket Sniperu jsem stihl zareagovat včas na uvolněné místo. A nic mě to nestálo!"
              </p>
              <p class="font-semibold text-text-primary">- Spokojený Sniper, dříve frustrovaný z nedostupných spojů RegioJet</p>
            </div>
            <div class="bg-background-body p-6 rounded-lg shadow-sm text-left">
              <p class="text-text-secondary italic mb-4">
                "Neuvěřitelná služba, ušetřila mi spoustu času a klikání. Potřebovala jsem sehnat lístek na vyprodaný RegioJet a tohle byla záchrana. Nastavila jsem si hlídání a za pár dní mi přišlo upozornění na volné místo. Ticket Sniper je můj hrdina! A je zdarma!"
              </p>
              <p class="font-semibold text-text-primary">- Nadšená Sniperka, která ví, co dělat když je RegioJet vyprodaný</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 5. Final CTA Section -->
      <section class="py-20 bg-primary text-text-on-primary">
        <div class="container mx-auto px-4 text-center">
          <h2 class="text-3xl font-bold mb-4">Nenechte si uniknout další volné místo na RegioJet!</h2>
          <p class="text-lg mb-8 max-w-2xl mx-auto">
            Připojte se k uživatelům, kteří už díky Ticket Sniper cestují na spojích, které se zdály být beznadějně vyprodané. Získejte notifikace na volná místa RegioJet a ulovte si ten svůj!
          </p>
          <RouterLink
            to="/register"
            class="inline-block px-8 py-3 min-h-[48px] bg-background-card text-primary rounded-lg hover:bg-background-alt text-lg font-semibold shadow-md transition duration-300"
          >
            Zaregistrovat se ZDARMA a začít lovit RegioJet lístky
          </RouterLink>
        </div>
      </section>
    </main>

    <!-- 6. Footer -->
    <footer class="bg-background-footer text-text-muted py-8">
      <div class="container mx-auto px-4 text-center">
        <div class="mb-4">
          <a href="mailto:info@ticketsniper.eu" class="mx-2">info@ticketsniper.eu</a>
          <!-- Links for Privacy Policy, Terms, Contact can be added here -->
          <!-- Example: <a href="/privacy" class="hover:text-white mx-2">Ochrana osobních údajů</a> -->
        </div>
        <p class="text-sm mb-4">
          © {{ currentYear }} Ticket Sniper. Všechna práva vyhrazena. Hlídač lístků RegioJet pro vaše pohodlí.
        </p>
        <p class="text-xs max-w-3xl mx-auto">
          Ticket Sniper je nezávislá a bezplatná služba, která není oficiálně provozována ani spojena se společností Regiojet a.s. ani žádným jiným dopravcem. Aplikace pouze monitoruje veřejně dostupné informace o spojích RegioJet, včetně jejich aktuální kapacity a dostupnosti volných míst. Samotný nákup jízdenek na spoje RegioJet probíhá výhradně na oficiálních stránkách dopravců.
        </p>
      </div>
    </footer>
  </div>
</template>
