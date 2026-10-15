import { useMemo } from "react";
import creerQr from "qrcode-generator";

/**
 * `CodeLivraison` — SPEC_ECRANS_FIGMA.md §2.10.
 *
 * Bloc centre, fond `surface`, **bordure 2 px en tirets `primaire`**, coins
 * 16. QR code 160 x 160, le code en style `Code` (32 Bold, interlettrage +4),
 * et « Montrez ce code au livreur ».
 *
 * Le QR est un vrai QR, genere a la volee et dessine en SVG : il encode le
 * code, donc un telephone qui le scanne lit bien `K7M-4PQ`. Un faux damier
 * aurait ete un decor, ce qu'interdit le §1.0 regle 7 — et il se serait vu au
 * premier scan devant un jury.
 */
export default function CodeLivraison({ code }: { code: string }) {
  const chemin = useMemo(() => {
    // Type 0 = version choisie automatiquement, correction « M ».
    const qr = creerQr(0, "M");
    qr.addData(code);
    qr.make();

    const cotes = qr.getModuleCount();
    const morceaux: string[] = [];
    for (let ligne = 0; ligne < cotes; ligne += 1) {
      for (let colonne = 0; colonne < cotes; colonne += 1) {
        if (qr.isDark(ligne, colonne)) {
          morceaux.push(`M${colonne} ${ligne}h1v1h-1z`);
        }
      }
    }
    return { d: morceaux.join(""), cotes };
  }, [code]);

  return (
    <div className="rounded-xl border-2 border-dashed border-primaire bg-white px-4 py-6 text-center">
      <p className="text-sm font-medium text-texte-secondaire">
        Votre code de livraison
      </p>

      <svg
        viewBox={`0 0 ${chemin.cotes} ${chemin.cotes}`}
        width={160}
        height={160}
        className="mx-auto mt-4"
        role="img"
        aria-label={`QR code du code de livraison ${code}`}
        shapeRendering="crispEdges"
      >
        <rect width={chemin.cotes} height={chemin.cotes} fill="#FFFFFF" />
        <path d={chemin.d} fill="#14181F" />
      </svg>

      <p className="mt-4 text-code leading-none font-bold tracking-[0.25rem] text-texte">
        {code}
      </p>

      <p className="mt-4 text-sm text-texte-secondaire">
        Montrez ce code au livreur, et à lui seul.
      </p>
    </div>
  );
}
