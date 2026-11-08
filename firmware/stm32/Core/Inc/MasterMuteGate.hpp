/******************************************************************************/
/**
 * @file MasterMuteGate.hpp
 * @brief Persistent remote mute composed with physical and transport gates.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 */
#ifndef MASTER_MUTE_GATE_HPP
#define MASTER_MUTE_GATE_HPP
class MasterMuteGate
{
public:
    void SetRemote(bool mute)
    {
        remote_ = mute;
    }
    bool Effective(bool physicalMute, bool transportReady) const
    {
        return remote_ || physicalMute || !transportReady;
    }
private:
    bool remote_ = false;
};
#endif
