import { redirect } from "next/navigation";

/** Special payment links are gone: Goldglitch is free. Anyone landing here goes to the app. */
export default function SpecialPayment() {
  redirect("/app");
}
