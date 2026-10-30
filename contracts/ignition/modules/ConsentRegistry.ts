import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const ConsentRegistryModule = buildModule("ConsentRegistryModule", (m) => {
  const consentRegistry = m.contract("ConsentRegistry");

  return { consentRegistry };
});

export default ConsentRegistryModule;
