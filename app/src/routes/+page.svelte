  <script lang="ts">
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';

    type SignalMessage = {
    kind: 'offer' | 'answer' | 'candidate';
    data: string;
    };

    let localVideoRef: HTMLVideoElement;
    let remoteVideoRef: HTMLVideoElement;
    let localStream: MediaStream;
    let remoteStream: MediaStream;
    let peerConnection: RTCPeerConnection;
    let ws: WebSocket;
    let roomId = writable<string>('');
    let inCall = writable<Boolean>(false);

    const servers = {
      iceServers: [
        {
          urls: 'stun:stun.l.google.com:19302'
        }
      ]
    };

    async function getRandomRoom() {
    const response = await fetch(`https://api.ogiggle.herjus.no/join_random_room`);
    const data = await response.json();
    roomId.set(data.room_id);
    return data.room_id;
    }

    onMount(async () => {
      localStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      localVideoRef.srcObject = localStream;
    })

    async function startCall() {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }

      const roomId = await getRandomRoom();
      ws = new WebSocket(`wss://api.ogiggle.herjus.no/ws/${roomId}`);

      ws.onmessage = handleSignalingMessage;

      ws.onopen = async () => {
        try {
          localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
          });
          localVideoRef.srcObject = localStream;
  
          peerConnection = new RTCPeerConnection(servers);
          localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
  
          peerConnection.ontrack = (event: RTCTrackEvent) => {
            remoteStream = event.streams[0];
            remoteVideoRef.srcObject = remoteStream;
          };
  
          peerConnection.onicecandidate = (event: RTCPeerConnectionIceEvent) => {
            if (event.candidate) {
              sendMessage({ kind: 'candidate', data: JSON.stringify(event.candidate) });
            }
          };
  
          const offer = await peerConnection.createOffer();
          await peerConnection.setLocalDescription(offer);
          sendMessage({ kind: 'offer', data: JSON.stringify(offer) });
  
          inCall.set(true);
        } catch (error) {
          throw new Error(JSON.stringify(error));
        }
      }
    }

    async function handleSignalingMessage(event: MessageEvent) {
      const message: SignalMessage = await JSON.parse(event.data);

      if (message.kind === 'offer') {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(JSON.parse(message.data)));
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        await sendMessage({ kind: 'answer', data: JSON.stringify(answer) });
      } else if (message.kind === 'answer') {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(JSON.parse(message.data)));
      } else if (message.kind === 'candidate') {
        await peerConnection.addIceCandidate(new RTCIceCandidate(JSON.parse(message.data)));
      }
    }

    function sendMessage(message: SignalMessage) {
      if (ws) {
        ws.send(JSON.stringify(message));
      }
    }

    function disconnectCall() {
      if (peerConnection) {
        peerConnection.close();
      }
      if (remoteStream) {
        remoteStream.getTracks().forEach(track => track.stop());
      }
      if (ws) {
        ws.close();
      }

      inCall.set(false);
    }

    function skipCall() {
      disconnectCall();
      startCall();
    }
  </script>

  <main class="min-h-screen max-h-screen h-screen flex flex-col">
      <header class="h-16 p-2 flex items-center">
          <img src="logo.png" alt="" class="h-full">
      </header>
      <div class="grid md:grid-cols-2 px-2 gap-2 mb-2">
        <div class="aspect-[4/3] flex items-center justify-center overflow-hidden bg-black/10 rounded">
          <video class="w-full" bind:this={remoteVideoRef} autoplay playsinline></video>
        </div>
        <div class="aspect-[4/3] flex items-center justify-center overflow-hidden bg-black/10 rounded">
            <video class="-scale-x-100 w-full " bind:this={localVideoRef} autoplay playsinline muted></video>
        </div>
      </div>
      <div class="grid md:grid-cols-2 px-2 gap-2 h-full pb-2">
          <div class="w-full space-y-2 flex flex-col">
            {#if !$inCall}
              <button on:click={startCall} class="w-full flex-1 bg-ogiggle-light disabled:bg-ogiggle-dark font-bold text-gray-50 text-3xl rounded p-2 border-b-8 border-ogiggle-dark disabled:border-ogiggle-light enabled:hover:scale-[98%] duration-200">Start</button>
            {:else}
              <button on:click={skipCall} class="w-full flex-1 bg-ogiggle-light disabled:bg-ogiggle-dark font-bold text-gray-50 text-3xl rounded p-2 border-b-8 border-ogiggle-dark disabled:border-ogiggle-light enabled:hover:scale-[98%] duration-200">Skip</button>
            {/if}
            <button disabled={!$inCall} on:click={disconnectCall} class="w-full h-1/2 bg-ogiggle-light disabled:bg-ogiggle-dark font-bold text-gray-50 text-3xl rounded p-2 border-b-8 border-ogiggle-dark disabled:border-ogiggle-light enabled:hover:scale-[98%] duration-200">Stop</button>
          </div>
          <div>
            <div class="h-full bg-black/10 rounded flex justify-between flex-col p-2">
              <div class="h-full bg-black/10 rounded flex justify-between flex-col p-2 box-border">
                <div class="flex flex-col-reverse h-full">
                  <p>for real</p>
                  <p>for real</p>
                  <p>for real</p>
                  <p>for real</p>
                  <p>for real</p>
                  <p>for real</p>
                  <p>for real</p>
                </div>
                <input class="w-full rounded p-2" type="text" placeholder="Type message...">
              </div>
          </div>
      </div>
  </main>