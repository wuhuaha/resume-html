import { createApp } from "vue";
import {
  Bot,
  BriefcaseBusiness,
  Download,
  FileText,
  Gauge,
  Github,
  Mail,
  MapPin,
  Mic,
  MicOff,
  Phone,
  Send,
  Settings,
  Sparkles,
  Upload,
} from "lucide-vue-next";

import App from "./App.vue";
import "./styles.css";

const app = createApp(App);

for (const [name, component] of Object.entries({
  Bot,
  BriefcaseBusiness,
  Download,
  FileText,
  Gauge,
  Github,
  Mail,
  MapPin,
  Mic,
  MicOff,
  Phone,
  Send,
  Settings,
  Sparkles,
  Upload,
})) {
  app.component(name, component);
}

app.mount("#app");
